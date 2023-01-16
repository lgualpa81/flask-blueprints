from flask import Blueprint, jsonify, request
from flask import current_app as app

paylink_v2_bp = Blueprint('paylink_v2', __name__)

from . import routes