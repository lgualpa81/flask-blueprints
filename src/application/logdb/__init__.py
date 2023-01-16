from flask import Blueprint, jsonify, request, json
from flask import current_app as app

logdb_bp = Blueprint('logdb', __name__)

from . import routes