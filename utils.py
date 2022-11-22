
from flask import Blueprint, request, make_response
import json
import datetime

#get datetime
def get_datetime():
    curTime = str(datetime.datetime.now())
    return curTime


# boat created json return
def boat_created(boat):
    responseContent = json.dumps(
        {"id": boat.key.id, 'name': boat['name'], 'type': boat['type'], 'length': boat['length'],'created': boat['created'],'loads': boat['loads'] ,'self': request.url+'/'+str(boat.key.id)})
    res = make_response(responseContent)
    res.mimetype = 'application/json'
    res.status_code = 201
    return res

#boat patched return
def boat_patched(boat):
    responseContent = json.dumps(
        {"id": boat.key.id, 'name': boat['name'], 'type': boat['type'], 'length': boat['length'],'modified': boat['modified'],'loads': boat['loads'] ,'self': request.url+'/'+str(boat.key.id)})
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

