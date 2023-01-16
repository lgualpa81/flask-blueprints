from . import mocks_bp, jsonify, request, app, json
from application.model import db, BaseHelper
from application.helper import tools
from application.messages import _MSG_ERR404, _MSG_ERR500, _MSG_NOPARAMS, _MSG_PAYLINK01, _MSG_PAYLINK02, _MSG_PAYLINK03, _MSG_BCKOFC01
from application.helper.decorator import jwt_optional_custom, jwt_required_custom


@backoffice_bp.route("/mocks/balance-transactions/balance_inquiry", methods=["POST"])
@jwt_optional_custom
def balance_inquiry():
    _djson = request.get_json()
    if set(('balance_type', 'merchant_id')) == set(_djson):
        balance_type = int(_djson["balance_type"])
        merchant_id = int(_djson["merchant_id"])

        qvat_rate = "SELECT case tax_rate when 0 then false else true end apply_iva FROM public.vat_rate WHERE active=true AND id=:vr"
        apply_iva = BaseHelper.get_one(
            qvat_rate, {"vr": vat_rate})['apply_iva']

        qch_method = "SELECT id, code, name FROM payment.charging_mode WHERE active=true AND juridical_person=:jp \
            AND apply_iva=:vat AND agreement_id=:ag AND country_id=:country_id"
        rch_method = BaseHelper.get_one(
            qch_method, {"jp": jp, "vat": apply_iva, "ag": agreement, "country_id": country_id})
        if rch_method is not None:
            cm_id = rch_method["id"]

            dcom_profile = {"merchant_id": merchant_id, "charging_mode_id": cm_id,
                            "status_id": constants.COM_PROFILE_PENDING_ID}
            r = BaseHelper.query(BaseHelper.generate_insert_placeholder(
                'payment.commerce_profile', dcom_profile.keys()), dcom_profile)
            if r.rowcount > 0:
                BaseHelper.query(BaseHelper.generate_insert_placeholder(
                    'payment.commerce_profile_log', dcom_profile.keys()), dcom_profile)
                dict_rst = {"code": 200, "message": "OK"}
            else:
                dict_rst = {"code": 500, "message": _MSG_ERR500}
        else:
            dict_rst = {"code": 404, "message": _MSG_BCKOFC01}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)