from flask import Blueprint, request
from google.cloud import datastore
from datetime import datetime
from utils import *
import json
import constants

client = datastore.Client()

bp = Blueprint('load', __name__, url_prefix='/loads')


@bp.route('', methods=['GET','POST'])
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


@bp.route('/<id>', methods=['DELETE','GET','PUT','PATCH'])
def loads_put_delete(id):

    # delete load and remove from boat
    if request.method == 'DELETE':
        load_key = client.key(constants.loads, int(id))
        load = client.get(key=load_key)
        if not load:
            return({"Error": "No load with this load_id exists"}, 404)

        # no loads on any boats to delete on kind:boats
        if len(load['carrier']) == 0:
            client.delete(key=load_key)
            return ('', 204)

        query = client.query(kind=constants.boats)  
        results = list(query.fetch())
        for e in results:
            if 'loads' in e.keys():
                for i in e['loads']:
                    if i['id'] == id:
                        e['loads'].remove(i)
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
            {"id": id, 'item': load['item'], 'volume': load['volume'], 'created': load['created'], 'modified': load['modified'],
             'carrier': carrierDisplay, 'self': request.url})
        res = make_response(responseContent)
        res.mimetype = 'application/json'
        res.status_code = 200
        return res

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
