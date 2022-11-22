from flask import Blueprint, request
from google.cloud import datastore
from utils import *
import json
import constants

client = datastore.Client()

bp = Blueprint('load', __name__, url_prefix='/loads')


@bp.route('', methods=['GET','POST','PUT', 'PATCH', 'DELETE'])
def loads():
    # create load
    if request.method == 'POST':
        content = request.get_json()

        new_load = datastore.entity.Entity(key=client.key(constants.loads))
        new_load.update(
            {"volume": content["volume"], 'item': content['item'], 'creation_date': content['creation_date'], 'carrier': None})
        client.put(new_load)
        load_key = client.key(constants.loads, int(new_load.key.id))
        load = client.get(key=load_key)
        returnJson = json.dumps(
            {"id": new_load.key.id, 'item': load['item'], 'volume': load['volume'], 'creation_date': load['creation_date'], 'carrier': load['carrier'], 'self': request.url+'/'+str(new_load.key.id)})
        return (returnJson, 201)
    # get all loads
    elif request.method == 'GET':
        query = client.query(kind=constants.loads)
        if not request.args:
            q_limit = 3
            q_offset = 0
        else:
            q_limit = int(request.args.get('limit', '3'))
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
            if e['carrier'] is not None:
                e['carrier']['self'] = request.root_url + \
                    'boats/' + e['carrier']['id']
                e['self'] = request.root_url + 'loads/' + str(e['id'])

        output = {"loads": results}
        if next_url:
            output["next"] = next_url

        returnJson = json.dumps(output)
        return (returnJson, 200)

    else:
        return 'Method not recogonized'


@bp.route('/<id>', methods=['DELETE', 'GET'])
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

        query = client.query(kind=constants.boats)  # was constant.boats
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
        returnJson = json.dumps(
            {"id": id, 'item': load['item'], 'volume': load['volume'], 'creation_date': load['creation_date'],
             'carrier': carrierDisplay, 'self': request.url})
        return (returnJson, 200)

    else:
        return 'Method not recogonized'
