from . import backoffice_bp, jsonify, request, app, json, constants
from application.model import db, BaseHelper
from application.helper import tools
from application.messages import _MSG_ERR404, _MSG_ERR500, _MSG_NOPARAMS, _MSG_BCKOFC01
from application.helper.decorator import jwt_optional_custom, jwt_required_custom
import math

def request_pagination():
    if 'page' in request.args and 'limit' in request.args:
        page = abs(int(request.args["page"]))
        limit = abs(int(request.args["limit"]))
        offset = (limit * page) - limit #do not put $limit*($page - 1)
        if (offset < 0): offset = 0
        if (limit > 500): limit = 10
    else:
        offset=0
        limit=10
        page=1

    return {"offset":offset, "page":page, "limit":limit}


@backoffice_bp.route("/backoffice/payment-profile/commerce-list", methods=["POST"])
@jwt_required_custom
def commerce_list():
    _djson = request.get_json()
    if set(('com_active', 'com_email', "cm_id", "com_name")) == set(_djson):
        com_active = _djson["com_active"]
        com_email = _djson["com_email"]
        com_name = _djson["com_name"]
        charging_mode_id = _djson["cm_id"]

        condicio = ""
        if com_active != "":
            condicio += "AND com_active=:p1 "
        if com_email:
            condicio += "AND com_email ilike :p2 "
        if com_name:
            condicio += "AND com_name ilike :p3 "
        if charging_mode_id:
            condicio += "AND cm_id=:p4 "

        pagination = request_pagination()
        page, offset, limit = pagination["page"], pagination["offset"], pagination["limit"]

        qpayment_profile = f"SELECT com_id, com_name, com_email, com_active, com_phone, docs, country, \
            cm_id, cm_name, cm_agreement, max_monthly_transactions, max_amount_per_link, max_daily_amount, \
            max_monthly_amount, count(*) over() as sql_count \
            FROM payment.view_commerce_payment_profile \
            WHERE 1=1 {condicio} ORDER BY 1 OFFSET {offset} LIMIT {limit}"

        qfilters = {"p1": com_active, "p2":"%" + tools.filter_string(com_email) + "%" ,
            "p3":"%" + tools.filter_string(com_name) + "%" , "p4":charging_mode_id}
        rpayment_profile = BaseHelper.get_all(qpayment_profile, qfilters)

        total_returned = len(rpayment_profile)
        if rpayment_profile is not None and total_returned>0:
            total_records = rpayment_profile[0]["sql_count"]
            total_pages = math.ceil(total_records / limit) if total_records > 0 else 0

            if (page > total_pages): page = total_pages
            dict_rst = {"code":200, "message": "OK", "data": rpayment_profile,
                "pagination":{"total_results":total_records, "total_pages":total_pages, "total_returned":total_returned, "current_page": page}}
        else:
            dict_rst = {"code":404 , "message": _MSG_BCKOFC01}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@backoffice_bp.route("/backoffice/payment-profile/charging-mode-list", methods=["POST"])
@jwt_required_custom
def charging_mode():
    _djson = request.get_json()
    if 'country_id' in _djson:
        country_id = _djson["country_id"]
        qcm = "SELECT cm.id as cm_id, cm.name as cm_name, cm.rate as cm_rate, \
                cm.fixed_charge as cm_fixed_charge, a.id as ag_id, a.name as ag_name \
            FROM payment.charging_mode cm inner join payment.agreement a on a.id=cm.agreement_id \
            WHERE cm.active=true and a.active =true AND cm.country_id=:p1 ORDER BY a.name"
        rcm = BaseHelper.get_all(qcm, {"p1":country_id})

        if rcm is not None and len(rcm)>0:
            dict_rst = {"code":200, "message": "OK", "data": rcm}
        else:
            dict_rst = {"code":404 , "message": _MSG_BCKOFC01}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@backoffice_bp.route("/backoffice/payment-profile/update", methods=["PUT"])
@jwt_required_custom
def update_profile():
    _djson = request.get_json()
    if set(('merchant_id', "current_profile_id", "new_profile_id", "sys_user_id")) == set(_djson):
        merchant_id = int(_djson["merchant_id"])
        current_profile_id = int(_djson["current_profile_id"])
        new_profile_id = int(_djson["new_profile_id"])
        sys_user_id = int(_djson["sys_user_id"])

        qprofile = "select * from payment.update_commerce_profile(:_p1, :_p2, :_p3, :_p4) as change_profile "
        rprofile = BaseHelper.get_one(qprofile, {"_p1":merchant_id, "_p2": current_profile_id, "_p3":new_profile_id, "_p4":sys_user_id})
        if rprofile is not None:
            _code = rprofile["change_profile"]

            if _code == 0: #ok
                dict_rst = {"code": 200, "message": "OK"}
            else:
                dict_rst = {"code": 500, "message": _MSG_ERR500}
        else:
            dict_rst = {"code":404 , "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)