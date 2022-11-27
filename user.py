from flask import Blueprint, request
from google.cloud import datastore
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

bp = Blueprint('user', __name__, url_prefix='/users')


@bp.route('', methods=['GET','POST','PUT', 'PATCH', 'DELETE'])
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

        