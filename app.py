from flask import *
from google.cloud import datastore
import constants
from utils import *

from six.moves.urllib.request import urlopen
#from flask_cors import cross_origin
from jose import jwt
#from os import environ as env
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from werkzeug.exceptions import HTTPException
#from dotenv import load_dotenv, find_dotenv

app = Flask(__name__)
client = datastore.Client()

# Update the values of the following 3 variables
app.secret_key = 'SECRET_KEY'
CLIENT_ID = 'pcEV9ftHGsGVOcqjwzSWrUIctFhhJ45w'
CLIENT_SECRET = '7WERr0QDEXhu3dTXGxtzztu0-HQi5_mC8uP-1Xu5-vL4gAAtMWMTOS6hC4sRYbSJ'
DOMAIN = 'andrew-vo-portfolio.us.auth0.com'
ALGORITHMS = ["RS256"]

oauth = OAuth(app)
auth0 = oauth.register(
    'auth0',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    api_base_url="https://" + DOMAIN,
    access_token_url="https://" + DOMAIN + "/oauth/token",
    authorize_url="https://" + DOMAIN + "/authorize",
    client_kwargs={
        'scope': 'openid profile email',
    },
    server_metadata_url=f'https://{DOMAIN}/.well-known/openid-configuration'
)

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

# Verify the JWT in the request's Authorization header
def verify_jwt(request):
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization'].split()
        token = auth_header[1]
    else:
        raise AuthError({"code": "no auth header",
                            "description":
                                "Authorization header is missing"}, 401)
    
    jsonurl = urlopen("https://"+ DOMAIN+"/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Invalid header. "
                            "Use an RS256 signed JWT Access Token"}, 401)
    if unverified_header["alg"] == "HS256":
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Invalid header. "
                            "Use an RS256 signed JWT Access Token"}, 401)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=CLIENT_ID,
                issuer="https://"+ DOMAIN+"/"
            )
        except jwt.ExpiredSignatureError:
            raise AuthError({"code": "token_expired",
                            "description": "token is expired"}, 401)
        except jwt.JWTClaimsError:
            raise AuthError({"code": "invalid_claims",
                            "description":
                                "incorrect claims,"
                                " please check the audience and issuer"}, 401)
        except Exception:
            raise AuthError({"code": "invalid_header",
                            "description":
                                "Unable to parse authentication"
                                " token."}, 401)

        return payload
    else:
        raise AuthError({"code": "no_rsa_key",
                            "description":
                                "No RSA key in JWKS"}, 401)

# Verify the JWT in the Auth0 User Creation
def verify_jwt_user_created(token):
    jsonurl = urlopen("https://"+ DOMAIN+"/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Invalid header. "
                            "Use an RS256 signed JWT Access Token"}, 401)
    if unverified_header["alg"] == "HS256":
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Invalid header. "
                            "Use an RS256 signed JWT Access Token"}, 401)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=CLIENT_ID,
                issuer="https://"+ DOMAIN+"/"
            )
        except jwt.ExpiredSignatureError:
            raise AuthError({"code": "token_expired",
                            "description": "token is expired"}, 401)
        except jwt.JWTClaimsError:
            raise AuthError({"code": "invalid_claims",
                            "description":
                                "incorrect claims,"
                                " please check the audience and issuer"}, 401)
        except Exception:
            raise AuthError({"code": "invalid_header",
                            "description":
                                "Unable to parse authentication"
                                " token."}, 401)

        return payload
    else:
        raise AuthError({"code": "no_rsa_key",
                            "description":
                                "No RSA key in JWKS"}, 401)

#########################
# AUTH0
#########################

@app.route('/')
def index():
    return render_template('index.html')

#Postman testing
@app.route('/decode', methods=['GET'])
def decode_jwt():
    payload = verify_jwt(request)
    return payload          

#ROUTES
@app.route('/login', methods=['GET'])
def login():    
    if request.method == 'GET':       
            #Auth0
            return oauth.auth0.authorize_redirect(
                #redirect_uri='https://portfolioproj-369315.uc.r.appspot.com/userinfo'
                redirect_uri='http://127.0.0.1:8080/userinfo'
            )

@app.route('/userinfo', methods = ['GET'])
def userinfo():
    token = oauth.auth0.authorize_access_token()
    payload = verify_jwt_user_created(token['id_token'])

    query = client.query(kind=constants.users)
    results = list(query.fetch())
    userExists = False
    for e in results:
        if e['sub'] == payload['sub']:
            userExists = True
            break
    if userExists is False:
        new_user = datastore.entity.Entity(key=client.key(constants.users))
        new_user.update({'sub': payload['sub']})
        client.put(new_user)

    return render_template('userinfo.html',jwtToken = token['id_token'], userSub = payload['sub'])

#########################
# USER
#########################
@app.route('/users', methods=['GET','POST','PUT', 'PATCH', 'DELETE'])
def users():  
    if request.method == 'GET':
        # unacceptable mime type
        if 'application/json' not in request.accept_mimetypes:
            res = req_unacceptable_mime_type()
            return res
        query = client.query(kind=constants.users)
        results = list(query.fetch())
        userArray = []
        for e in results:
            userArray.append(e)
        res = user_return(userArray)
        return res

#########################
# BOAT
#########################

@app.route('/boats', methods=['GET','POST'])
def boats():
    #Create a boat
    if request.method == 'POST':
        # if request content type is not application/json
        if request.content_type != "application/json":
            res = req_incorrect_content()
            return res
        # unacceptable mime type
        if 'application/json' not in request.accept_mimetypes:
            res = req_unacceptable_mime_type()
            return res

        payload = verify_jwt(request)

        content = request.get_json()
        creation_time = get_datetime()
        new_boat = datastore.entity.Entity(
            key=client.key(constants.boats))
        new_boat.update({'name': content['name'],
                         'type': content['type'], 'length': content['length'], 'loads': [], 'created': creation_time, 'modified': None, 'owner': payload['sub']})
        client.put(new_boat)

        boat_key = client.key(constants.boats, int(new_boat.key.id))
        boat = client.get(key=boat_key)
        res = boat_created(boat)
        return res

    #get all auth boats
    elif request.method == 'GET':
        # unacceptable mime type
        if 'application/json' not in request.accept_mimetypes:
            res = req_unacceptable_mime_type()
            return res
        
        payload = verify_jwt(request)

        query = client.query(kind=constants.boats)

        if not request.args:
            q_limit = 5
            q_offset = 0
        else:
            q_limit = int(request.args.get('limit', '5'))
            q_offset = int(request.args.get('offset', '0'))
        l_iterator = query.fetch(limit=q_limit, offset=q_offset)
        pages = l_iterator.pages
        results = list(next(pages))
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + \
                str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None

        boatArray = []
        for e in results:
            if e['owner'] == payload['sub']:
                e["id"] = e.key.id
                for i in e['loads']:
                    i['self'] = request.root_url + 'loads/' + i['id']
                e['self'] = request.root_url + 'boats/' + str(e['id'])
                boatArray.append(e)
        output = {"boats": boatArray}
    
        if next_url:
            output["next"] = next_url

        returnJson = json.dumps(output)
        return (returnJson, 200)

    else:
        res = method_not_permitted()
        return res


@app.route('/boats/<id>', methods=['GET','PUT','PATCH', 'DELETE'])
def boats_put_patch_delete(id):
    # delete specific boat and unload
    if request.method == 'DELETE':

        

        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)
        if not boat:
            return({"Error": "No boat with this boat_id exists"}, 404)

        payload = verify_jwt(request)
        if boat['owner'] != payload['sub']:
            res = forbidden_content()
            return res

        # no loads on any boats to delete on kind:boats
        if len(boat['loads']) == 0:
            client.delete(key=boat_key)
            return ('', 204)

        query = client.query(kind=constants.loads)
        results = list(query.fetch())
        modified_time = get_datetime()
        for e in results:
            if e['carrier']['id'] == id:
                e.update({"carrier": None, 'modified': modified_time})
                client.put(e)
        client.delete(key=boat_key)
        return ('', 204)

    #patch a specific boat
    elif request.method == 'PATCH':
        # if request content type is not application/json
        if request.content_type != "application/json":
            res = req_incorrect_content()
            return res
        # unacceptable mime type
        if 'application/json' not in request.accept_mimetypes:
            res = req_unacceptable_mime_type()
            return res

        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)
        content = request.get_json()

        payload = verify_jwt(request)
        if boat['owner'] != payload['sub']:
            res = forbidden_content()
            return res
        
        # update only keys present
        for key in content:
            boat.update({f'{key}': content[key]})
        modified_time = get_datetime()
        boat.update({'modified': modified_time})
        client.put(boat)

        # response content must be application/json with modified object
        res = boat_patched(boat)
        return res
    
    #put a specific boat
    elif request.method == 'PUT':
        # if request content type is not application/json
        if request.content_type != "application/json":
            res = req_incorrect_content()
            return res
        # unacceptable mime type
        if 'application/json' not in request.accept_mimetypes:
            res = req_unacceptable_mime_type()
            return res

        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)
        content = request.get_json()

        payload = verify_jwt(request)
        if boat['owner'] != payload['sub']:
            res = forbidden_content()
            return res
        
        # update only keys present
        for key in content:
            boat.update({f'{key}': content[key]})
        modified_time = get_datetime()
        boat.update({'modified': modified_time})
        client.put(boat)

        # response content must be application/json with modified object
        res = boat_patched(boat)
        return res

    #get specific boat with id to see loads
    elif request.method == 'GET':
        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)

        payload = verify_jwt(request)
        if boat['owner'] != payload['sub']:
            res = forbidden_content()
            return res

        if not boat:
            return ({"Error": "No boat with this boat_id exists"}, 404)

        res = boat_return(boat)
        return res

    else:
        res = method_not_permitted()
        return res


#Boat/Loads functionality
@app.route('/boats/<bid>/loads/<lid>', methods=['PUT', 'DELETE'])
def add_delete_load(bid, lid):
    # assign load to boat
    if request.method == 'PUT':
        boat_key = client.key(constants.boats, int(bid))
        boat = client.get(key=boat_key)
        if not boat:
            return ({'Error': "The specified boat and/or load does not exist"}, 404)
        load_key = client.key(constants.loads, int(lid))
        load = client.get(key=load_key)
        if not load:
            return ({'Error': "The specified boat and/or load does not exist"}, 404)
        if load['carrier'] is not None:
            res = already_loaded()
            return res

        if 'loads' in boat.keys():
            boat['loads'].append(
                {'id': str(load.id)})
        else:
            boat['loads'] = [
                {'id': str(load.id)}]
        modified_time = get_datetime()
        load.update({'carrier': {'id': bid}, 'modified': modified_time})
        boat.update({'modified': modified_time})
        client.put(load)
        client.put(boat)
        return('', 204)

    # remove load from boat
    if request.method == 'DELETE':
        boat_key = client.key(constants.boats, int(bid))
        boat = client.get(key=boat_key)
        if not boat:
            return ({'Error': "No boat with this boat_id is loaded with the load with this load_id"}, 404)
        load_key = client.key(constants.loads, int(lid))
        load = client.get(key=load_key)
        if not load:
            return ({'Error': "No boat with this boat_id is loaded with the load with this load_id"}, 404)

        if 'loads' in boat.keys():
            initialLen = len(boat['loads'])
            for i in range(len(boat['loads'])):
                if boat['loads'][i]['id'] == lid:
                    boat['loads'].remove(boat['loads'][i])
            afterLen = len(boat['loads'])
            if initialLen == afterLen:
                return ({'Error': "No boat with this boat_id is loaded with the load with this load_id"}, 404)
        modified_time = get_datetime()
        if 'carrier' in load.keys():
            load.update({'carrier': None, 'modified': modified_time})
        boat.update({'modified':modified_time})    
        client.put(load)
        client.put(boat)
        return('', 204)
    else:
        res = method_not_permitted()
        return res

#########################
# LOADS
#########################
@app.route('/loads', methods=['GET','POST'])
def loads():
    # create load
    if request.method == 'POST':
        # if request content type is not application/json
        if request.content_type != "application/json":
            res = req_incorrect_content()
            return res
        # unacceptable mime type
        if 'application/json' not in request.accept_mimetypes:
            res = req_unacceptable_mime_type()
            return res

        content = request.get_json()
        creation_time = get_datetime()
        new_load = datastore.entity.Entity(key=client.key(constants.loads))
        new_load.update(
            {"volume": content["volume"], 'item': content['item'], 'created': creation_time,'modified': None, 'carrier': None})
        client.put(new_load)
        load_key = client.key(constants.loads, int(new_load.key.id))
        load = client.get(key=load_key)
        res = load_created(load)
        return res

    # get all loads
    elif request.method == 'GET':
        # unacceptable mime type
        if 'application/json' not in request.accept_mimetypes:
            res = req_unacceptable_mime_type()
            return res

        query = client.query(kind=constants.loads)
        if not request.args:
            q_limit = 5
            q_offset = 0
        else:
            q_limit = int(request.args.get('limit', '5'))
            q_offset = int(request.args.get('offset', '0'))
        l_iterator = query.fetch(limit=q_limit, offset=q_offset)
        pages = l_iterator.pages
        results = list(next(pages))
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + \
                str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None

        for e in results:
            e["id"] = e.key.id
            e['self'] = request.root_url + 'loads/' + str(e['id'])

        output = {"loads": results}
        if next_url:
            output["next"] = next_url

        returnJson = json.dumps(output)
        return (returnJson, 200)

    else:
        res = method_not_permitted()
        return res


#########################
# SPECIFIC LOAD
#########################

@app.route('/loads/<id>', methods=['DELETE','GET','PUT','PATCH'])
def loads_put_delete(id):

    # delete load and remove from boat
    if request.method == 'DELETE':
        load_key = client.key(constants.loads, int(id))
        load = client.get(key=load_key)
        if not load:
            return({"Error": "No load with this load_id exists"}, 404)

        # no loads on any boats to delete on kind:boats
        if load['carrier'] is None:
            client.delete(key=load_key)
            return ('', 204)

        query = client.query(kind=constants.boats)  
        results = list(query.fetch())
        modified_time = get_datetime()
        
        for e in results:
            if 'loads' in e.keys():
                for i in e['loads']:
                    if i['id'] == id:
                        e['loads'].remove(i)
                        e['modified'] = modified_time
                        client.put(e)
        client.delete(key=load_key)
        return ('', 204)

    # get specific load with id
    elif request.method == 'GET':
        # unacceptable mime type
        if 'application/json' not in request.accept_mimetypes:
            res = req_unacceptable_mime_type()
            return res
            
        load_key = client.key(constants.loads, int(id))
        load = client.get(key=load_key)
        if not load:
            return ({"Error": "No load with this load_id exists"}, 404)
        if load['carrier'] == None:
            carrierDisplay = None
        else:
            carrierDisplay = load['carrier']
            carrierID = carrierDisplay['id']
            carrierDisplay['self'] = request.root_url+'boats/' + carrierID
        
        responseContent = json.dumps(
            {"id": int(id), 'item': load['item'], 'volume': load['volume'], 'created': load['created'], 'modified': load['modified'],
             'carrier': carrierDisplay, 'self': request.url})
        res = make_response(responseContent)
        res.mimetype = 'application/json'
        res.status_code = 200
        return res

    #patch specific load id
    elif request.method == 'PATCH':
        # if request content type is not application/json
        if request.content_type != "application/json":
            res = req_incorrect_content()
            return res
        # unacceptable mime type
        if 'application/json' not in request.accept_mimetypes:
            res = req_unacceptable_mime_type()
            return res

        load_key = client.key(constants.loads, int(id))
        load = client.get(key=load_key)
        content = request.get_json()
        
        # update only keys present
        for key in content:
            load.update({f'{key}': content[key]})
        modified_time = get_datetime()
        load.update({'modified': modified_time})
        client.put(load)

        # response content must be application/json with modified object
        res = load_patched(load)
        return res
    
    #put specific load id
    elif request.method == 'PUT':
        # if request content type is not application/json
        if request.content_type != "application/json":
            res = req_incorrect_content()
            return res
        # unacceptable mime type
        if 'application/json' not in request.accept_mimetypes:
            res = req_unacceptable_mime_type()
            return res

        load_key = client.key(constants.loads, int(id))
        load = client.get(key=load_key)
        content = request.get_json()
        
        # update only keys present
        for key in content:
            load.update({f'{key}': content[key]})
        modified_time = get_datetime()
        load.update({'modified': modified_time})
        client.put(load)

        # response content must be application/json with modified object
        res = load_patched(load)
        return res

    else:
        res = method_not_permitted()
        return res


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
