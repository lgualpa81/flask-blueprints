from . import paylink_v2_bp, jsonify, request, app
from .. import constants
import json
from flask import g
from application.model import db, BaseHelper
from application.helper import tools, crypt
from application.messages import _MSG_ERR404, _MSG_ERR500, _MSG_NOPARAMS, _MSG_PAYLINK01, _MSG_PAYLINK02, _MSG_PAYLINK03
from application.helper.decorator import jwt_optional_custom, jwt_required_custom


@paylink_v2_bp.route("/preview", methods=["POST"])
@jwt_required_custom
def preview_payment():
    _djson = request.get_json()

    if set(('merchant_id', "source", "amount", "vat_id", "cost_buyer", "fingerprint", "user_id", "description")) == set(_djson):
        merchant_id = _djson["merchant_id"]
        source = int(_djson["source"])
        amount = float(_djson["amount"])
        vat_id = int(_djson["vat_id"])
        cost_buyer = bool(int(_djson["cost_buyer"]))
        user_id = int(_djson["user_id"])
        description = _djson["description"]

        qamounts = "SELECT document FROM payment.calculate_fee(:c, :m, :cb, :vat)"
        ramounts = BaseHelper.get_one(
            qamounts, {"c": merchant_id, "m": amount, "cb": cost_buyer, "vat": vat_id})

        if ramounts is not None and (ramounts["document"].get("result") is None):
            qcommerce_p = "SELECT * FROM payment.get_merchant_profile(:c)"
            rcommerce_p = BaseHelper.get_one(
                qcommerce_p, {"c": merchant_id})["document"]
            charging_mode_id = rcommerce_p["charging_mode_id"]
            frequency = rcommerce_p["unit_duration"]
            duration = rcommerce_p["duration_per_link"]
            currency_id, country_id = rcommerce_p["currency_id"], rcommerce_p["country_id"]
            link_max_amount = rcommerce_p["max_amount_per_link"]

            amount_detail = ramounts["document"]
            amount_due = amount_detail["monto_cobrar"]
            tax = amount_detail["valor_iva"]
            comision = amount_detail["comision"]
            deposit_amount = amount_detail["monto_depositar"]
            base_amount = amount_detail["valor_base"]

            if amount_due <= link_max_amount:
                dict_rst = {"code": 200, "message": "OK",
                            "data": {"amount_due": amount_due, "untaxed_amount": amount, "base_amount": base_amount,
                                     "fee": comision, "tax": tax, "deposit_amount": deposit_amount}}
            else:
                dict_rst = {"code": 300, "message": _MSG_PAYLINK02}
        else:
            dict_rst = {
                "code": 205, "message": "El comercio no cuenta con un perfil de cobro habilitado"}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@paylink_v2_bp.route("/generate", methods=["POST"])
@jwt_required_custom
def send_payment():
    _djson = request.get_json()

    if set(('merchant_id', "source", "amount", "vat_id", "cost_buyer", "fingerprint", "user_id", "description")) == set(_djson):
        merchant_id = _djson["merchant_id"]
        source = int(_djson["source"])
        amount = float(_djson["amount"])
        vat_id = int(_djson["vat_id"])
        cost_buyer = bool(int(_djson["cost_buyer"]))
        user_id = int(_djson["user_id"])
        description = _djson["description"]

        qamounts = "SELECT document FROM payment.calculate_fee(:c, :m, :cb, :vat)"
        ramounts = BaseHelper.get_one(
            qamounts, {"c": merchant_id, "m": amount, "cb": cost_buyer, "vat": vat_id})

        if ramounts is not None and (ramounts["document"].get("result") is None):
            qcommerce_p = "SELECT * FROM payment.get_merchant_profile(:c)"
            rcommerce_p = BaseHelper.get_one(
                qcommerce_p, {"c": merchant_id})["document"]
            charging_mode_id = rcommerce_p["charging_mode_id"]
            frequency = rcommerce_p["unit_duration"]
            duration = rcommerce_p["duration_per_link"]
            currency_id, country_id = rcommerce_p["currency_id"], rcommerce_p["country_id"]
            link_max_amount = rcommerce_p["max_amount_per_link"]

            texpires_at = tools.future_utc(frequency, duration)

            amount_detail = ramounts["document"]
            amount_due = amount_detail["monto_cobrar"]
            tax = amount_detail["valor_iva"]

            if amount_due <= link_max_amount:
                ticket_number = tools.generate_ticket_number()
                crypt_tn = crypt.obscure(ticket_number.encode())

                dtx = {"merchant_id": merchant_id, "transaction_group_id": 1,
                       "country_id": country_id, "untaxed_amount": amount, "amount_due": amount_due,
                       "status_id": constants.TX_PENDING, "crypt_ticket_number": crypt_tn, "source_id": source,
                       "charging_mode_id": charging_mode_id, "currency_id": currency_id, "cost_buyer": cost_buyer,
                       "amount_detail": json.dumps(amount_detail), "tax": tax, "fingerprint": json.dumps(_djson["fingerprint"]),
                       "ticket_number": ticket_number, "ticket_expires_at": texpires_at, "user_id": user_id, "description": description}
                dp = tools.daily_parity()
                rtx = BaseHelper.query(BaseHelper.generate_insert_placeholder(
                    f'payment.transaction_{dp}', dtx.keys()), dtx)

                # Creo un registro para el historial de la transaccion
                dtlog = {"merchant_id": merchant_id,
                         "status_id": constants.TX_PENDING, "ticket_number": ticket_number}
                BaseHelper.query(BaseHelper.generate_insert_placeholder(
                    'payment.transaction_log', dtlog.keys()), dtlog)

                if rtx.rowcount > 0:
                    url_checkout = app.config["URL_CHECKOUT_WEB"].replace(
                        "<TK>", crypt_tn)
                    dict_rst = {"code": 200, "message": "OK", "data": {
                        "amount_due": amount_due, "ticket_number": crypt_tn, "url_checkout": url_checkout}}
                else:
                    dict_rst = {"code": 500, "message": _MSG_ERR500}
            else:
                dict_rst = {"code": 300, "message": _MSG_PAYLINK02}
        else:
            dict_rst = {
                "code": 205, "message": "El comercio no cuenta con un perfil de cobro habilitado"}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)
