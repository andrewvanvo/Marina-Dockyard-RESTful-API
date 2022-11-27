
from flask import Blueprint, request, make_response
import json
import datetime

#get datetime
def get_datetime():
    curTime = str(datetime.datetime.now())
    return curTime

#user return
def user_return(userArray):
    responseContent = []
    for user in userArray:
        entry = {"User Database ID": user.key.id, 'User Sub':user['sub']}
        responseContent.append(entry)
    converted = json.dumps(responseContent)
    res = make_response(converted)
    res.mimetype = 'application/json'
    res.status_code = 200
    return res

# boat created return
def boat_created(boat):
    responseContent = json.dumps(
        {"id": boat.key.id, 'name': boat['name'], 'type': boat['type'], 'length': boat['length'],'created': boat['created'],
        'modified':boat['modified'],'loads': boat['loads'] ,'self': request.url+'/'+str(boat.key.id)})
    res = make_response(responseContent)
    res.mimetype = 'application/json'
    res.status_code = 201
    return res

#boat patched return
def boat_patched(boat):
    responseContent = json.dumps(
        {"id": boat.key.id, 'name': boat['name'], 'type': boat['type'], 'length': boat['length'],'created': boat['created'],
        'modified': boat['modified'],'loads': boat['loads'] ,'self': request.url+'/'+str(boat.key.id)})
    res = make_response(responseContent)
    res.mimetype = 'application/json'
    res.status_code = 200
    return res

#boat load return
def boat_return(boat, load):
    responseContent = json.dumps(
        {"id": boat.key.id, 'name': boat['name'], 'type': boat['type'], 'length': boat['length'],'created': boat['created'],
        'modified': boat['modified'],'loads': boat['loads'] ,'self': request.url+'/'+str(boat.key.id)})
    
    res = make_response(responseContent)
    res.mimetype = 'application/json'
    res.status_code = 200
    return res

# load created return
def load_created(load):
    responseContent = json.dumps(
        {"id": load.key.id, "volume": load["volume"], 'item': load['item'], 'created': load['created'],
        'modified': load['modified'], 'carrier': load['carrier'], 'self': request.url+'/'+str(load.key.id)})
    res = make_response(responseContent)
    res.mimetype = 'application/json'
    res.status_code = 201
    return res

#load patched return
def load_patched(load):
    responseContent = json.dumps(
        {"id": load.key.id, "volume": load["volume"], 'item': load['item'], 'created': load['created'],
        'modified': load['modified'], 'carrier': load['carrier'], 'self': request.url+'/'+str(load.key.id)})
    res = make_response(responseContent)
    res.mimetype = 'application/json'
    res.status_code = 200
    return res

# incorrect req content type
def req_incorrect_content():
    responseContent = json.dumps({
        "Error": "The request object has the incorrect content type"})
    res = make_response(responseContent)
    res.mimetype = 'application/json'
    res.status_code = 400
    return res

# unacceptable MIME type 406 
def req_unacceptable_mime_type():
    responseContent = json.dumps({
        "Error": "Server can not send the requested MIME type"})
    res = make_response(responseContent)
    res.mimetype = 'application/json'
    res.status_code = 406
    return res

# method not allowed at url
def method_not_permitted():
    responseContent = json.dumps({
        "Error": "Method not permitted at this location"})
    res = make_response(responseContent)
    res.mimetype = 'application/json'
    res.status_code = 405
    return res

# forbidden content
def forbidden_content():
    responseContent = json.dumps({
        "Error": "The request object has requested forbidden content"})
    res = make_response(responseContent)
    res.mimetype = 'application/json'
    res.status_code = 403
    return res

# load already loaded
def already_loaded():
    responseContent = json.dumps({
        "Error": "The load is already loaded on another boat"})
    res = make_response(responseContent)
    res.mimetype = 'application/json'
    res.status_code = 403
    return res

