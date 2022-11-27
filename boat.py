from flask import Blueprint, request
from google.cloud import datastore
from datetime import datetime
from utils import *
import json
import constants


from six.moves.urllib.request import urlopen
#from flask_cors import cross_origin
from jose import jwt
#from os import environ as env
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from werkzeug.exceptions import HTTPException
#from dotenv import load_dotenv, find_dotenv

client = datastore.Client()

bp = Blueprint('boat', __name__, url_prefix='/boats')


@bp.route('', methods=['GET','POST'])
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

        

        content = request.get_json()
        creation_time = get_datetime()
        new_boat = datastore.entity.Entity(
            key=client.key(constants.boats))
        new_boat.update({'name': content['name'],
                         'type': content['type'], 'length': content['length'], 'loads': [], 'created': creation_time, 'modified': None})
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
        for e in results:
            e["id"] = e.key.id
            for i in e['loads']:
                i['self'] = request.root_url + 'loads/' + i['id']
            e['self'] = request.root_url + 'boats/' + str(e['id'])

        output = {"boats": results}
        if next_url:
            output["next"] = next_url

        returnJson = json.dumps(output)
        return (returnJson, 200)

    else:
        res = method_not_permitted()
        return res


@bp.route('/<id>', methods=['GET','PUT','PATCH', 'DELETE'])
def boats_put_patch_delete(id):
    # delete specific boat and unload
    if request.method == 'DELETE':
        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)
        if not boat:
            return({"Error": "No boat with this boat_id exists"}, 404)

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
    #elif request.method == 'GET':
    #    boat_key = client.key(constants.boats, int(id))
    #    boat = client.get(key=boat_key)
    #    if not boat:
    #        return ({"Error": "No boat with this boat_id exists"}, 404)
    #    if len(boat['loads']) == 0:
    #        loadDisplay = []
    #    else:
    #        loadDisplay = boat['loads']
    #        loadID = loadDisplay[0]['id']
    #        loadDisplay[0]['self'] = request.root_url+'loads/' + loadID
    #    
    #    res = boat_return(boat, loadDisplay)

    else:
        res = method_not_permitted()
        return res


#Boat/Loads functionality
@bp.route('/<bid>/loads/<lid>', methods=['PUT', 'DELETE'])
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


