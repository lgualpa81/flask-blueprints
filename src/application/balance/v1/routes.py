from . import balance_v1_bp, jsonify, request, app
import json
import math
from flask import g
from .sql import Balance
from application.helper import tools, paginate
from application.helper.pdf import Voucher
from application.messages import _MSG_ERR404, _MSG_ERR500, _MSG_NOPARAMS, _MSG_PAYLINK01, _MSG_PAYLINK02, _MSG_PAYLINK03
from application.helper.decorator import jwt_optional_custom, jwt_required_custom


@balance_v1_bp.route("/overview", methods=["POST"])
@jwt_required_custom
def bl_v1_overview():
    _djson = request.get_json()

    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        merchant_id = _djson["merchant_id"]
        role_id = _djson["role_id"]
        user_id = _djson["user_id"]

        if role_id != 4:
            user_id = 0

        reg_customers = Balance.get_regular_customers(merchant_id)
        payable_balance = Balance.get_payable_balance(
            merchant_id, user_id)["saldo"]
        total_transactions = Balance.get_payable_total_transactions(
            merchant_id, user_id)["total"]

        dict_rst = {"code": 200, "message": "OK",
                    "data": {"payable_balance": payable_balance,
                             "customers": reg_customers,
                             "total_transactions": total_transactions}}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@balance_v1_bp.route("/statistics/daily", methods=["POST"])
@jwt_required_custom
def bl_v1_statistics_daily():
    _djson = request.get_json()
    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        merchant_id = _djson["merchant_id"]
        role_id = _djson["role_id"]
        user_id = _djson["user_id"]

        if role_id != 4:
            user_id = 0

        bl_daily = Balance.get_balance_daily(merchant_id, user_id)

        if bl_daily is not None and bl_daily["total"] is not None:
            cash_flow = bl_daily["total"]
            transactions = bl_daily["transactions"]

            data = {"chash_flow": cash_flow, "detail": transactions}

            dict_rst = {"code": 200, "message": "OK", "data": data}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@balance_v1_bp.route("/statistics/monthly", methods=["POST"])
@jwt_required_custom
def bl_v1_statistics_monthly():
    _djson = request.get_json()
    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        merchant_id = _djson["merchant_id"]
        role_id = _djson["role_id"]
        user_id = _djson["user_id"]

        if role_id != 4:
            user_id = 0

        bl_monthly = Balance.get_balance_monthly(merchant_id, user_id)

        if len(bl_monthly) > 0 and bl_monthly is not None:
            cash_flow = 0
            for t in bl_monthly:
                cash_flow += t["total"]

            data = {"chash_flow": cash_flow, "detail": bl_monthly}

            dict_rst = {"code": 200, "message": "OK", "data": data}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@balance_v1_bp.route("/statistics/yearly", methods=["POST"])
@jwt_required_custom
def bl_v1_statistics_yearly():
    _djson = request.get_json()
    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        merchant_id = _djson["merchant_id"]
        role_id = _djson["role_id"]
        user_id = _djson["user_id"]

        if role_id != 4:
            user_id = 0

        bl_yearly = Balance.get_balance_yearly(merchant_id, user_id)
        if bl_yearly is not None and bl_yearly["total"] is not None:
            cash_flow = bl_yearly["total"]
            transactions = bl_yearly["transactions"]

            data = {"chash_flow": cash_flow, "detail": transactions}

            dict_rst = {"code": 200, "message": "OK", "data": data}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@balance_v1_bp.route("/payable-balance", methods=["POST"])
@jwt_required_custom
def bl_v1_payable():
    _djson = request.get_json()
    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        merchant_id = _djson["merchant_id"]
        role_id = _djson["role_id"]
        user_id = _djson["user_id"]

        if role_id != 4:
            user_id = 0

        amount_payable = Balance.get_approved_balance(
            merchant_id, user_id)["saldo"]
        dict_rst = {"code": 200, "message": "OK",
                    "data": {"amount_payable": amount_payable}}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@balance_v1_bp.route("/payable-balance/order", methods=["POST"])
@jwt_required_custom
def bl_v1_payable_order():
    _djson = request.get_json()
    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        merchant_id = _djson["merchant_id"]
        role_id = _djson["role_id"]
        user_id = _djson["user_id"]

        if role_id != 4:
            user_id = 0

        payable_token = tools.random_string(15)
        rs_payable = Balance.get_payable_order(
            merchant_id, user_id, payable_token)

        if rs_payable["code"] == 200:
            dict_rst = {"code": 200, "message": "OK", "token": payable_token}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@balance_v1_bp.route("/transactions/latest-approved", methods=["POST"])
@jwt_required_custom
def bl_v1_latest_approved():
    _djson = request.get_json()

    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        merchant_id = _djson["merchant_id"]
        role_id = _djson["role_id"]
        user_id = _djson["user_id"]

        if role_id != 4:
            user_id = 0

        pagination = paginate.request_pagination()
        page, limit = pagination["page"], pagination["limit"]

        rlatest_approved = Balance.get_transaction_latest_approved(
            merchant_id, user_id, pagination)
        total_returned = len(rlatest_approved)
        if rlatest_approved is not None and total_returned > 0:
            bpagination = paginate.build_pagination(
                rlatest_approved, page, limit)
            rs, rs_paginate = bpagination["data"], bpagination["pagination"]

            dict_rst = {"code": 200, "message": "OK", "data": rs,
                        "pagination": rs_paginate}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@balance_v1_bp.route("/payable-balance/activity", methods=["POST"])
@jwt_required_custom
def bl_v1_payable_activity():
    _djson = request.get_json()
    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        merchant_id = _djson["merchant_id"]
        role_id = _djson["role_id"]
        user_id = _djson["user_id"]

        if role_id != 4:
            user_id = 0

        pagination = paginate.request_pagination()
        page, limit = pagination["page"], pagination["limit"]

        ractivity = Balance.get_payable_activity(
            merchant_id, user_id, pagination)
        total_returned = len(ractivity)
        if ractivity is not None and total_returned > 0:
            bpagination = paginate.build_pagination(
                ractivity, page, limit)
            rs, rs_paginate = bpagination["data"], bpagination["pagination"]

            dict_rst = {"code": 200, "message": "OK", "data": rs,
                        "pagination": rs_paginate}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@balance_v1_bp.route("/transactions/activity-summary", methods=["POST"])
@jwt_required_custom
def bl_v1_activity_summary():
    _djson = request.get_json()

    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        merchant_id = _djson["merchant_id"]
        role_id = _djson["role_id"]
        user_id = _djson["user_id"]

        if role_id != 4:
            user_id = 0

        pagination = paginate.request_pagination()
        page, limit = pagination["page"], pagination["limit"]

        rsummary = Balance.get_transaction_activity_summary(
            merchant_id, user_id, pagination)
        total_returned = len(rsummary)
        if rsummary is not None and total_returned > 0:
            bpagination = paginate.build_pagination(rsummary, page, limit)
            rs, rs_paginate = bpagination["data"], bpagination["pagination"]

            dict_rst = {"code": 200, "message": "OK", "data": rs,
                        "pagination": rs_paginate}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


def calc_amount_retained(amount_detail):
    # comision + comision iva
    total_comision = amount_detail["total_comision"]
    total_tax = amount_detail["retefuente"] + \
        amount_detail["reteiva"]+amount_detail["reteica"]
    return total_tax+total_comision


@balance_v1_bp.route("/transactions/detail", methods=["POST"])
@jwt_required_custom
def bl_v1_trans_detail():
    _djson = request.get_json()
    if set(('merchant_id', 'trans_id')) == set(_djson):
        # sku: stock keep unit
        merchant_id = _djson["merchant_id"]
        trans_id = _djson["trans_id"]

        rs_tdetail = Balance.get_detail_transaction(merchant_id, trans_id)
        if rs_tdetail is not None:
            country_id, currency = rs_tdetail["country_id"], rs_tdetail["currency"]
            amount_paid = rs_tdetail["amount_due"]
            amount_detail = rs_tdetail["amount_detail"]

            amount_payable = amount_detail["monto_depositar"] if 'monto_depositar' in amount_detail else 0
            amount_iva = amount_detail["valor_iva"] if 'valor_iva' in amount_detail else 0
            impoconsumo = amount_detail["impoconsumo"] if 'impoconsumo' in amount_detail else 0
            comision = amount_detail["total_comision"] if 'total_comision' in amount_detail else 0
            retefuente = amount_detail["retefuente"] if 'retefuente' in amount_detail else 0
            reteiva = amount_detail["reteiva"] if 'reteiva' in amount_detail else 0
            reteica = amount_detail["reteica"] if 'reteica' in amount_detail else 0

            sku, paid_date = rs_tdetail["sku"], rs_tdetail["paid_date"]
            customer_name, customer_lname = rs_tdetail["customer_names"], rs_tdetail["customer_last_names"]
            status = rs_tdetail["status"]

            amount_retained = 0
            if country_id == 1:
                amount_retained = calc_amount_retained(amount_detail)

            data = {"customer_names": customer_name, "customer_last_names": customer_lname,
                    "trans_id": trans_id,
                    "status": status,
                    "paid_date": paid_date,
                    "amount_due": amount_paid,
                    "amount_retained": amount_retained,
                    "amount_payable": amount_payable,
                    "currency": currency,
                    "tax": {
                        "amount_iva": amount_iva,
                        "impoconsumo": impoconsumo,
                        "retefuente": retefuente,
                        "reteiva": reteiva,
                        "reteica": reteica
                    },
                    "fee": comision,
                    "sku": sku}
            dict_rst = {"code": 200, "message": "OK", "data": data}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}

    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@balance_v1_bp.route("/transactions/voucher-detail", methods=["POST"])
@jwt_required_custom
def bl_v1_trans_voucher():
    _djson = request.get_json()
    if set(('merchant_id', 'trans_id')) == set(_djson):
        # sku: stock keep unit
        merchant_id = _djson["merchant_id"]
        trans_id = _djson["trans_id"]

        rs_vdetail = Balance.get_voucher_detail(merchant_id, trans_id)
        if rs_vdetail is not None:
            country_id, currency = rs_vdetail["country_id"], rs_vdetail["currency"]

            amount_paid, amount_detail = rs_vdetail["amount_paid"], rs_vdetail["amount_detail"]
            untaxed_amount = rs_vdetail["untaxed_amount"]
            payable_amount = amount_detail["monto_depositar"] if 'monto_depositar' in amount_detail else 0
            taxable_income = amount_detail['valor_base_iva'] if 'valor_base_iva' in amount_detail else 0
            iva = amount_detail['valor_iva'] if 'valor_iva' in amount_detail else 0
            outcome_metadata = rs_vdetail["outcome_metadata"]
            error_detail = ' | '.join(outcome_metadata['errors']) if 'errors' in outcome_metadata else ''

            psp_reference = rs_vdetail["psp_reference"]
            psp_pos = rs_vdetail["psp_pos"]

            pos_code = psp_pos["code"] if 'code' in psp_pos else ''
            pos_terminal = psp_pos["terminal"] if 'terminal' in psp_pos else ''

            sku, paid_date = rs_vdetail["sku"], rs_vdetail["paid_date"]
            customer_name, customer_lname = rs_vdetail["customer_names"], rs_vdetail["customer_last_names"]
            description, status = rs_vdetail["description"], rs_vdetail["status"]

            data = {"customer_names": customer_name, "customer_lastnames": customer_lname, "trans_id": trans_id,
                    "paid_date": paid_date, "amount_paid": amount_paid, "currency": currency, "iva": iva,
                    "unique_code": pos_code, "terminal": pos_terminal, "transaction_number": psp_reference,
                    "taxable_income": taxable_income, "net_amount": untaxed_amount, "reference": psp_reference,
                    "description": description, "status": status, "details": error_detail,
                    "sku": sku, "total_balance": payable_amount}

            _voucher_data = data.copy()
            _voucher_data["merchant_id"] = merchant_id
            _voucher_data["paid_date"] = tools.dt_voucher(paid_date)

            file_voucher = Voucher().generate_voucher(_voucher_data)

            dict_rst = {"code": 200, "message": "OK",
                        "data": data, "file_voucher": file_voucher}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}

    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@balance_v1_bp.route("/transactions/latest-payout", methods=["POST"])
@jwt_required_custom
def bl_v1_payout():
    _djson = request.get_json()
    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        merchant_id = _djson["merchant_id"]
        role_id = _djson["role_id"]
        user_id = _djson["user_id"]

        if role_id != 4:
            user_id = 0

        pagination = paginate.request_pagination()
        page, limit = pagination["page"], pagination["limit"]

        rsummary = Balance.get_transaction_latest_payout(
            merchant_id, user_id, pagination)
        total_returned = len(rsummary)
        if rsummary is not None and total_returned > 0:
            bpagination = paginate.build_pagination(rsummary, page, limit)
            rs, rs_paginate = bpagination["data"], bpagination["pagination"]

            dict_rst = {"code": 200, "message": "OK", "data": rs,
                        "pagination": rs_paginate}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)
