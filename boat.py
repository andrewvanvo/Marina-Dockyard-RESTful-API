from flask import Blueprint, request
from google.cloud import datastore
from datetime import datetime
from utils import *
import json
import constants

client = datastore.Client()

bp = Blueprint('boat', __name__, url_prefix='/boats')


@bp.route('', methods=['GET','POST'])
def boats():
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
                         'type': content['type'], 'length': content['length'], 'loads': [], 'created': creation_time})
        client.put(new_boat)

        boat_key = client.key(constants.boats, int(new_boat.key.id))
        boat = client.get(key=boat_key)
        res = boat_created(boat)
        return res

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


@bp.route('/<id>', methods=['PUT','PATCH', 'DELETE'])
def boats_put_patch_delete(id):
    # delete specific boat and unload
    if request.method == 'DELETE':
        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)
        if not boat:
            return({"Error": "No boat with this boat_id exists"}, 404)

        query = client.query(kind=constants.loads)
        results = list(query.fetch())
        for e in results:
            if e['carrier']['id'] == id:
                e.update({"carrier": None})
                client.put(e)
        client.delete(key=boat_key)
        return ('', 204)

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


    # get specific boat with id
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
    #    returnJson = json.dumps(
    #        {"id": id, 'name': boat['name'], 'type': boat['type'],
    #         'length': boat['length'], 'loads': loadDisplay, 'self': request.url}
    #    )
    #    return (returnJson, 200)
    else:
        res = method_not_permitted()
        return res


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
            return ({'Error': "The load is already loaded on another boat"}, 403)
        if 'loads' in boat.keys():
            boat['loads'].append(
                {'id': str(load.id)})
        else:
            boat['loads'] = [
                {'id': str(load.id)}]
        load.update({'carrier': {'id': bid}})
        client.put(load)
        client.put(boat)
        return('', 204)
    # delete load from boat

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
            # boat['loads'].remove(int(lid))
            initialLen = len(boat['loads'])
            for i in range(len(boat['loads'])):
                if boat['loads'][i]['id'] == lid:
                    boat['loads'].remove(boat['loads'][i])
            afterLen = len(boat['loads'])
            if initialLen == afterLen:
                return ({'Error': "No boat with this boat_id is loaded with the load with this load_id"}, 404)

        if 'carrier' in load.keys():
            load.update({'carrier': None})
        client.put(load)
        client.put(boat)
        return('', 204)
    else:
        return 'Method not recogonized'


@bp.route('/<id>/loads', methods=['GET'])
# get all loads for a given boat
def get_all_loads(id):
    if request.method == 'GET':
        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)
        if not boat:
            return ({'Error': "No boat with this boat_id exists"}, 404)

        if 'loads' in boat.keys():
            modifiedLoads = boat['loads']
            if len(boat['loads']) != 0:
                for i in modifiedLoads:
                    i['self'] = request.root_url + 'loads/' + i['id']

        returnJson = json.dumps(
            {"id": boat.key.id, 'name': boat['name'], 'type': boat['type'],
             'length': boat['length'], 'loads': modifiedLoads, 'self': request.url+'/' + id})

        return (returnJson, 200)
    else:
        return 'Method not recogonized'
