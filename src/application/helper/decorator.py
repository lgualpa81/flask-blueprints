from functools import wraps
from flask import jsonify, request, g
from flask import current_app as app
from . import tools
import json

def jwt_required_custom(fn):
    '''
    Middleware JWT required
    '''
    @wraps(fn)
    def wrapper(*args, **kwargs):
        headers = request.headers
        if ("X-Auth" in headers) and len(headers['X-Auth'])>0 :
            url = app.config['URL_AUTH_COMMERCE_CHECK_JWT']
            dextra = {"http_method":"POST", "headers": {'Content-Type':'application/json',
                "X-Auth": headers["X-Auth"]}}
            if g.request_id != "":
                dextra["headers"]["X-Request-ID"] = g.request_id
            check_result = tools.call_endpoint(url, {}, **dextra)
            if check_result["status_code"] != 200:
                message = check_result['resp_json']['msg'] if 'msg' in check_result['resp_json'] else check_result['resp_json']['message']
                return jsonify({'code': 401, 'message': message}), 401
            else:
                tk_identity = json.loads(tools.decode_b64(
                    check_result['resp_json']['data']))  # generado en commerce.auth.login
                if 'correlation_id' in tk_identity:
                    g.log_correlationid = tk_identity["correlation_id"]
                if 'request_id' in tk_identity:
                    g.request_id = tk_identity["request_id"]
            return fn(*args, **kwargs)
        else:
            return jsonify({'code': 401, 'message': 'Unauthorized'}), 401
    return wrapper


def jwt_optional_custom(fn):
    '''
    Middleware JWT optional
    '''
    @wraps(fn)
    def wrapper(*args, **kwargs):
        headers = request.headers
        if ("X-Auth" in headers) and len(headers['X-Auth'])>0 :
            url = app.config['URL_AUTH_COMMERCE_CHECK_JWT']
            dextra = {"http_method":"POST", "headers": {'Content-Type':'application/json',
                "X-Auth": headers["X-Auth"]}}
            if g.request_id != "":
                dextra["headers"]["X-Request-ID"] = g.request_id
            check_result = tools.call_endpoint(url, {}, **dextra)
            if check_result["status_code"] != 200:
                message = check_result['resp_json']['msg'] if 'msg' in check_result['resp_json'] else check_result['resp_json']['message']
                return jsonify({'code': 401, 'message': message}), 401
            else:
                tk_identity = json.loads(tools.decode_b64(
                    check_result['resp_json']['data']))  # generado en commerce.auth.login
                if 'correlation_id' in tk_identity:
                    g.log_correlationid = tk_identity["correlation_id"]
                if 'request_id' in tk_identity:
                    g.request_id = tk_identity["request_id"]
        return fn(*args, **kwargs)
    return wrapper


def fresh_jwt_required_custom(fn):
    '''
    Middleware JWT required
    '''
    @wraps(fn)
    def wrapper(*args, **kwargs):
        headers = request.headers
        if ("X-Refresh-Auth" in headers) and len(headers['X-Refresh-Auth'])>0 :
            url = app.config['URL_AUTH_COMMERCE_REFRESH_JWT']
            dextra = {"http_method":"POST", "headers": {'Content-Type':'application/json',
                "X-Auth": headers["X-Refresh-Auth"]}}
            check_result = tools.call_endpoint(url, {}, **dextra)
            if check_result["status_code"] != 200:
                message = check_result['resp_json']['msg'] if 'msg' in check_result['resp_json'] else check_result['resp_json']['message']
                return jsonify({'code': 401, 'message': message}), 401
            g.decorator_new_jwt = check_result["resp_headers"]["X-Auth"]
            return fn(*args, **kwargs)
        else:
            return jsonify({'code': 401, 'message': 'Unauthorized'}), 401
    return wrapper

