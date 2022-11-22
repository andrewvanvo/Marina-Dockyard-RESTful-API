from flask import Blueprint, request
from google.cloud import datastore
from utils import *
import json
import constants

client = datastore.Client()

bp = Blueprint('user', __name__, url_prefix='/users')


@bp.route('', methods=['GET','POST','PUT', 'PATCH', 'DELETE'])
def users():  
    pass