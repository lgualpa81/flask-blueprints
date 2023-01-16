from . import mock_bp, jsonify, request, app
from application.messages import _MSG_ERR404, _MSG_ERR500, _MSG_NOPARAMS
from application.helper.decorator import jwt_optional_custom, jwt_required_custom


@mock_bp.route("/balance/overview", methods=["POST"])
@jwt_required_custom
def bl_overview():
    _djson = request.get_json()
    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        customers = [{"customer_id": 1, "names": "Sara", "last_names": "Kent"},
                     {"customer_id": 2, "names": "Kevin", "last_names": "Tyler"}]
        data = {"outstading_balance": 26056000,
                "user_logged": "Juan Pablo", "customers": customers}
        dict_rst = {"code": 200, "message": "OK", "data": data}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@mock_bp.route("/balance/statistics/daily", methods=["POST"])
@jwt_required_custom
def bl_statistics_daily():
    _djson = request.get_json()
    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        data = {"chash_flow": 80000,
                "detail": [{"date": "2021-04-20", "amount": 720456},
                           {"date": "2021-03-01", "amount": 20456}]}
        dict_rst = {"code": 200, "message": "OK", "data": data}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@mock_bp.route("/balance/statistics/monthly", methods=["POST"])
@jwt_required_custom
def bl_statistics_monthly():
    _djson = request.get_json()
    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        data = {"chash_flow": 180000,
                "detail": [{"month": "2021-04", "total": 150000,
                            "transactions": [{"day": 1, "amount": 25000}, {"day": 15, "amount": 125000}]},
                           {"month": "2021-03", "total": 30000,
                            "transactions": [{"day": 9, "amount": 5000}, {"day": 15, "amount": 15000}, {"day": 29, "amount": 10000}]}]}
        dict_rst = {"code": 200, "message": "OK", "data": data}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@mock_bp.route("/balance/statistics/yearly", methods=["POST"])
@jwt_required_custom
def bl_statistics_yearly():
    _djson = request.get_json()
    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        data = {"chash_flow": 3180000,
                "detail": [{"year": 2021, "total": 2720456},
                           {"year": 2020, "total": 329544},
                           {"year": 2019, "total": 130000}]}
        dict_rst = {"code": 200, "message": "OK", "data": data}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@mock_bp.route("/balance/outstanding", methods=["POST"])
@jwt_required_custom
def bl_outstanding():
    _djson = request.get_json()
    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        data = {"tax": {"rete_iva": 4057, "rete_ica": 403, "rete_fuente": 50},
                "fee": 608,
                "balance_outstanding": 251222,
                "currency": "USD"}
        dict_rst = {"code": 200, "message": "OK", "data": data}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@mock_bp.route("/balance/request-payment", methods=["POST"])
@jwt_required_custom
def bl_request_payment():
    _djson = request.get_json()
    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        dict_rst = {"code": 200, "message": "OK"}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@mock_bp.route("/balance/transactions/latest-approved", methods=["POST"])
@jwt_required_custom
def bl_approved():
    _djson = request.get_json()
    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        limit = request.args['limit'] if 'limit' in request.args and isinstance(
            request.args.get('limit', type=int), int) else 10
        data = [{"customer_names": "Joe", "customer_lastnames": "Doe", "txid": 1,
                 "paid_date": "2021-04-15 14:45", "amount_paid": 1450000, "currency": "USD"},
                {"customer_names": "Kevin", "customer_lastnames": "Tyler", "txid": 2,
                 "paid_date": "2021-04-15 13:17 ", "amount_paid": 15000, "currency": "USD"},
                {"customer_names": "Joe", "customer_lastnames": "Doe", "txid": 3,
                 "paid_date": "2021-04-10 21:00 ", "amount_paid": 10000, "currency": "USD"},
                {"customer_names": "Sara", "customer_lastnames": "Kent", "txid": 4,
                 "paid_date": "2021-04-10 13:17 ", "amount_paid": 15000, "currency": "USD"},
                {"customer_names": "Kevin", "customer_lastnames": "Tyler", "txid": 5,
                 "paid_date": "2021-04-09 13:17 ", "amount_paid": 15000, "currency": "USD"},
                {"customer_names": "Roger", "customer_lastnames": "Ponce", "txid": 6,
                 "paid_date": "2021-04-09 13:17 ", "amount_paid": 15000, "currency": "USD"},
                {"customer_names": "Kevin", "customer_lastnames": "Tyler", "txid": 7,
                 "paid_date": "2021-04-05 13:17 ", "amount_paid": 15000, "currency": "USD"},
                {"customer_names": "Kevin", "customer_lastnames": "Tyler", "txid": 8,
                 "paid_date": "2021-04-04 13:17 ", "amount_paid": 15000, "currency": "USD"},
                {"customer_names": "Steve", "customer_lastnames": "Pearson", "txid": 9,
                 "paid_date": "2021-04-15 13:17 ", "amount_paid": 15000, "currency": "USD"},
                {"customer_names": "Kevin", "customer_lastnames": "Tyler", "txid": 10,
                 "paid_date": "2021-04-15 13:17 ", "amount_paid": 15000, "currency": "USD"}]
        dict_rst = {"code": 200, "message": "OK", "data": data}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@mock_bp.route("/balance/transactions/activity-summary", methods=["POST"])
@jwt_required_custom
def bl_summary():
    _djson = request.get_json()
    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        limit = request.args['limit'] if 'limit' in request.args and isinstance(
            request.args.get('limit', type=int), int) else 10
        data = [{"customer_names": "Joe", "customer_lastnames": "Doe", "txid": 1,
                 "paid_date": "2021-04-15 14:45", "amount_paid": 1450000, "currency": "USD"},
                {"customer_names": "Kevin", "customer_lastnames": "Tyler", "txid": 2,
                 "paid_date": "2021-04-15 13:17 ", "amount_paid": 15000, "currency": "USD"},
                {"customer_names": "Joe", "customer_lastnames": "Doe", "txid": 3,
                 "paid_date": "2021-04-10 21:00 ", "amount_paid": 10000, "currency": "USD"},
                {"customer_names": "Sara", "customer_lastnames": "Kent", "txid": 4,
                 "paid_date": "2021-04-10 13:17 ", "amount_paid": 15000, "currency": "USD"},
                {"customer_names": "Kevin", "customer_lastnames": "Tyler", "txid": 5,
                 "paid_date": "2021-04-09 13:17 ", "amount_paid": 15000, "currency": "USD"},
                {"customer_names": "Roger", "customer_lastnames": "Miller", "txid": 6,
                 "paid_date": "2021-04-09 13:17 ", "amount_paid": 15000, "currency": "USD"},
                {"customer_names": "Kevin", "customer_lastnames": "Tyler", "txid": 7,
                 "paid_date": "2021-04-05 13:17 ", "amount_paid": 15000, "currency": "USD"},
                {"customer_names": "Kevin", "customer_lastnames": "Tyler", "txid": 8,
                 "paid_date": "2021-04-04 13:17 ", "amount_paid": 15000, "currency": "USD"},
                {"customer_names": "Steve", "customer_lastnames": "Pearson", "txid": 9,
                 "paid_date": "2021-04-15 13:17 ", "amount_paid": 15000, "currency": "USD"},
                {"customer_names": "Kevin", "customer_lastnames": "Tyler", "txid": 10,
                 "paid_date": "2021-04-15 13:17 ", "amount_paid": 15000, "currency": "USD"}]
        dict_rst = {"code": 200, "message": "OK", "data": data}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@mock_bp.route("/balance/transactions/detail", methods=["POST"])
@jwt_required_custom
def bl_trans_detail():
    _djson = request.get_json()
    if set(('merchant_id', 'trans_id')) == set(_djson):
        # sku: stock keep unit
        data = {"customer_names": "Joe", "customer_lastnames": "Doe", "txid": 1,
                "paid_date": "2021-04-15 14:45", "amount_paid": 250000, "currency": "USD",
                "sku": "M989394", "amount_retained": 17806, "total_balance": 232194}
        dict_rst = {"code": 200, "message": "OK", "data": data}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@mock_bp.route("/balance/transactions/voucher-detail", methods=["POST"])
@jwt_required_custom
def bl_trans_voucher():
    _djson = request.get_json()
    if set(('merchant_id', 'trans_id')) == set(_djson):
        # sku: stock keep unit
        data = {"customer_names": "Joe", "customer_lastnames": "Doe", "txid": 1,
                "paid_date": "2021-04-15 14:45", "amount_paid": 250000, "currency": "USD",
                "unique_code": "014248256", "terminal": "00003398", "transaction_number": "2456743",
                "taxable_income": 250000, "net_amount": 250000, "reference": "23956",
                "description": "Pago", "status": "APROBADA", "details": "Número de orden aceptada",
                "sku": "M989394", "total_balance": 232194}
        dict_rst = {"code": 200, "message": "OK", "data": data}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@mock_bp.route("/balance/transactions/latest-payout", methods=["POST"])
@jwt_required_custom
def bl_payout():
    _djson = request.get_json()
    if set(('merchant_id', 'role_id', "user_id")) == set(_djson):
        data = [{"payout_date": "2021-04-15 14:45", "amount_payout": 2046000, "currency": "USD", "txid": 20},
                {"payout_date": "2021-04-10 13:17 ", "amount_payout": 1066000, "currency": "USD", "txid": 21}]
        dict_rst = {"code": 200, "message": "OK", "data": data}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)
