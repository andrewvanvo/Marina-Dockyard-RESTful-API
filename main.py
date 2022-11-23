from flask import *
from google.cloud import datastore
import boat
import load
import user
import constants

from six.moves.urllib.request import urlopen
#from flask_cors import cross_origin
from jose import jwt
from os import environ as env
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv, find_dotenv

app = Flask(__name__)
app.secret_key = 'SECRET_KEY'
client = datastore.Client()

app.register_blueprint(boat.bp)
app.register_blueprint(load.bp)
app.register_blueprint(user.bp)

# Update the values of the following 3 variables
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

#https://auth0.com/docs/quickstart/backend/python/01-authorization?_ga=2.46956069.349333901.1589042886-466012638.1589042885#create-the-jwt-validation-decorator

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

#def verify_jwt_get_boat(request):
#    if 'Authorization' in request.headers:
#        auth_header = request.headers['Authorization'].split()
#        token = auth_header[1]
#    
#    jsonurl = urlopen("https://"+ DOMAIN+"/.well-known/jwks.json")
#    jwks = json.loads(jsonurl.read())
#    try:
#        unverified_header = jwt.get_unverified_header(token)
#    except:
#        payload = "invalid"
#        return payload
#    rsa_key = {}
#    for key in jwks["keys"]:
#        if key["kid"] == unverified_header["kid"]:
#            rsa_key = {
#                "kty": key["kty"],
#                "kid": key["kid"],
#                "use": key["use"],
#                "n": key["n"],
#                "e": key["e"]
#            }
#    if rsa_key:
#        try:
#            payload = jwt.decode(
#                token,
#                rsa_key,
#                algorithms=ALGORITHMS,
#                audience=CLIENT_ID,
#                issuer="https://"+ DOMAIN+"/"
#            )
#        except:
#            payload = 'invalid'
#            return payload
#        return payload
#    else:
#        payload = 'invalid'
#        return payload


#######################################################
# AUTH0
#######################################################

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
                redirect_uri='http://127.0.0.1:8080/callback'
            )
@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token

    return redirect('http://127.0.0.1:8080/userinfo')

@app.route('/userinfo', methods = ['GET'])
def userinfo():
    jwtToken = session.get('user')
    print(jwtToken['id_token'])
    return render_template('userinfo.html',jwtToken = jwtToken['id_token'])

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
