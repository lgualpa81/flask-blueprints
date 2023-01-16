from . import paylink_bp, jsonify, request, app, json, constants
from flask import g
from application.model import db, BaseHelper
from application.helper import tools, crypt
from application.messages import _MSG_ERR404, _MSG_ERR500, _MSG_NOPARAMS, _MSG_PAYLINK01, _MSG_PAYLINK02, _MSG_PAYLINK03
from application.helper.decorator import jwt_optional_custom, jwt_required_custom


@paylink_bp.route("/paylink/send-payment", methods=["POST"])
@jwt_required_custom
def send_payment():
    _djson = request.get_json()

    if set(('merchant_id', "source", "amount", "test_mode", "cost_buyer", "fingerprint", "user_id", "description")) == set(_djson):
        merchant_id = _djson["merchant_id"]
        source = int(_djson["source"])
        amount = float(_djson["amount"])
        test_mode = bool(_djson["test_mode"])
        cost_buyer = bool(int(_djson["cost_buyer"]))
        user_id = int(_djson["user_id"])
        description = _djson["description"]

        qamounts = "SELECT document FROM payment.calculate_fee(:c, :m, :cb)"
        ramounts = BaseHelper.get_one(
            qamounts, {"c": merchant_id, "m": amount, "cb": cost_buyer})

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
                       "status_id": constants.TX_PENDING, "crypt_ticket_number": crypt_tn, "test_mode": test_mode, "source_id": source,
                       "charging_mode_id": charging_mode_id, "currency_id": currency_id, "cost_buyer": cost_buyer,
                       "amount_detail": json.dumps(amount_detail), "tax": tax, "fingerprint": _djson["fingerprint"],
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


@paylink_bp.route("/psp/checkout-web/get-payment/<string:crypt_tn>", methods=["GET"])
def get_payment_psp(crypt_tn):
    '''
    Informacion de la transaccion usada por los modulos: PSP, checkout-web
    '''
    if len(crypt_tn) > 0:
        tn = crypt.unobscure(crypt_tn)
        if tn is not False:
            g.log_correlationid = tn
            qtx = f"SELECT * FROM payment.transaction_getinfo(:tn)"
            rtx = BaseHelper.get_one(qtx, {"tn": tn})

            if rtx is not None:
                doc = rtx["document"]
                amount_due, status_id, status = (
                    doc["amount_due"], doc["status_id"], doc["status"])
                tax, valid_tk, tname = (
                    doc["tax"], doc["valid_token"], doc['tname'])
                country_id, description = doc["country_id"], doc["description"]
                amount_detail, result_md = doc["amount_detail"], doc["outcome_metadata"]
                errors = result_md["errors"] if result_md is not None and ('errors' in result_md) else ''

                # status_id: 9->Pendiente, 10->token expirado
                if status_id == constants.TX_PENDING:
                    if bool(valid_tk):
                        data = {"amount_due": amount_due, "tax": tax, "status": status,
                                "tn": tn, "country_id": country_id,
                                "description": description, "amount_detail": amount_detail}
                        dict_rst = {"code": 200, "message": "OK", "data": data}
                    else:
                        qupd = "SELECT * FROM payment.transaction_update_status(:tn, ':st_id', :tname)"
                        BaseHelper.query(
                            qupd, {"tn": tn, "st_id": constants.TX_TK_EXPIRED, "tname": tname})

                        dict_rst = {"code": 300, "message": _MSG_PAYLINK01}
                elif status_id == constants.TX_TK_EXPIRED:
                    dict_rst = {"code": 300, "message": _MSG_PAYLINK01}
                else:
                    paid_dt_tz, approval_code = doc["paid_dt_tz"], doc["approval_code"]
                    untaxed_amount, currency = doc["untaxed_amount"], doc["currency"]

                    data = {"amount_due": amount_due, "tax": tax, "untaxed_amount": untaxed_amount,
                            "ticket_number": tn, "currency": currency, "approval_code": approval_code,
                            "amount_detail": amount_detail, "errors": errors,
                            "description": description, "paid_date": paid_dt_tz}
                    dict_rst = {"code": 210, "message": status, "data": data}
            else:
                dict_rst = {"code": 404, "message": _MSG_ERR404}
        else:
            dict_rst = {"code": 404, "message": _MSG_PAYLINK03}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)

# ==== IPAY ================


@paylink_bp.route("/paylink/ipay-order-register/<string:crypt_tn>", methods=["PUT"])
def ipay_order_register(crypt_tn):
    _djson = request.get_json()
    tn = crypt.unobscure(crypt_tn)
    if len(tn) > 0 and len(_djson) > 0:
        qtx = "SELECT * FROM payment.transaction_getinfo(:tn)"
        rtx = BaseHelper.get_one(qtx, {"tn": tn})

        if rtx is not None:
            doc = rtx["document"]
            tname = doc["tname"]
            ipay_order = _djson["ipay_order"]

            dorder_metadata = {"psp_order_metadata": json.dumps(
                ipay_order), "updated_at": tools.current_utc()}

            condicio = "ticket_number=:tn"
            qorder = BaseHelper.generate_update_placeholder(
                f'payment.{tname}', dorder_metadata.keys(), condicio)
            bparams_condicio = {"tn": tn}
            dorder_metadata.update(bparams_condicio)
            rorder = BaseHelper.query(qorder, dorder_metadata)

            if rorder.rowcount > 0:
                dict_rst = {"code": 200, "message": "OK"}
            else:
                dict_rst = {"code": 500, "message": _MSG_ERR500}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


def mkt_event_approved_transaction(payload):
    try:
        merchant_id = payload["merchant_id"]
        amount_due = payload["amount_due"]

        qcommerce = "SELECT c.email as com_email, c.name as com_name, u.first_name || ' ' || u.last_name as com_seller \
                FROM commerce.commerce c INNER JOIN commerce.commerce_user_account cu on c.id=cu.merchant_id \
                    INNER JOIN commerce.user_account u  on u.id = cu.user_account_id \
                WHERE c.active =true and cu.active =true and u.active =true and u.role_id =2 and c.id=:com_id"
        r_commerce = BaseHelper.get_one(qcommerce, {"com_id": merchant_id})

        if r_commerce is not None:
            com_email = r_commerce["com_email"]
            com_name = r_commerce["com_name"]
            com_seller = r_commerce["com_seller"]

            _url_notification = app.config['MKT_CRM_NOTIFICATION']
            _pl_notification = {"event": "approved_payment",
                                "payload": {"com_email": com_email, "currency": "USD", "amount": amount_due, "com_name": com_name, "com_seller": com_seller}}
            tools.call_endpoint(_url_notification, _pl_notification)
    except Exception as e:
        print("Oops! mkt_event_approved_transaction ", e.__class__, "occurred.")
        message = [str(x) for x in e.args]
        print(message)


def create_customer(email, kfields):
    tcustomers = "public.customers"
    qcustomer = f"SELECT id, email FROM {tcustomers} WHERE active=true AND email=:e"
    rcustomer = BaseHelper.get_one(qcustomer, {"e": email})
    if rcustomer is None:
        rins_customer = BaseHelper.query(BaseHelper.generate_insert_placeholder(
            tcustomers, kfields.keys()), kfields)
        return rins_customer.first()[0]
    return rcustomer['id']


@paylink_bp.route("/paylink/ipay-confirm/<string:ticket_number>", methods=["PUT"])
def ipay_confirm(ticket_number):
    _djson = request.get_json()
    if len(ticket_number) > 0 and len(_djson) > 0:
        qtx = "SELECT * FROM payment.transaction_getinfo(:tn)"
        rtx = BaseHelper.get_one(qtx, {"tn": ticket_number})

        if rtx is not None:
            doc = rtx["document"]
            tname, amount_due, merchant_id = doc["tname"], doc["amount_due"], doc["merchant_id"]
            ipay_code, ipay_rsp = _djson["code"], _djson["weft"]

            dconfirm = {"psp_id": constants.PSP_CREDI,
                        "updated_at": tools.current_utc()}
            if 'cardAuthInfo' in ipay_rsp:
                buyer_name = ipay_rsp["cardAuthInfo"]["cardholderName"]
                buyer_email = ipay_rsp["payerData"]["email"]
                dconfirm["buyer"] = json.dumps(
                    {"name": buyer_name, "email": buyer_email})

            if ipay_code == "0":
                approval_code = ipay_rsp['cardAuthInfo']['approvalCode']
                tx_status_id = constants.TX_PSP_APPROVED
                dconfirm.update({"psp_approval_code": approval_code, "masked_number": ipay_rsp["cardAuthInfo"]["maskedPan"],
                                 "status_id": tx_status_id, "paid_date": tools.current_utc()})
            else:
                tx_status_id = constants.TX_PSP_REJECTED
                dconfirm.update({"status_id": tx_status_id})

            condicio = "ticket_number=:tn"
            q_confirm = BaseHelper.generate_update_placeholder(
                f'payment.{tname}', dconfirm.keys(), condicio)
            bparams_condicio = {"tn": ticket_number}
            dconfirm.update(bparams_condicio)
            r_confirm = BaseHelper.query(q_confirm, dconfirm)

            # Creo un registro para el historial de la transaccion
            dtlog = {"merchant_id": merchant_id,
                     "status_id": tx_status_id, "ticket_number": ticket_number}
            BaseHelper.query(BaseHelper.generate_insert_placeholder(
                'payment.transaction_log', dtlog.keys()), dtlog)

            if r_confirm.rowcount > 0:
                if ipay_code == "0":
                    # Task queue MKT Active Campaign
                    payload_approved = {
                        "merchant_id": merchant_id, "amount_due": amount_due}
                    mkt_event_approved_transaction(payload_approved)

                dict_rst = {"code": 200, "message": "OK"}
            else:
                dict_rst = {"code": 500, "message": _MSG_ERR500}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@paylink_bp.route("/callback/card/checkout-charge", methods=["POST"])
def callback_card_charge():
    _djson = request.get_json()

    psp_code, tn = _djson['code'], _djson["tn"]
    ldigits, buyer = _djson["ldigits"], _djson["buyer"]
    approval_code, psp_id = _djson["approval_code"], _djson["psp_id"]
    buyer_fingerprint = _djson["buyer_fingerprint"]
    outcome_metadata = _djson["psp_outcome"]
    psp_pos = _djson["merchant"]

    g.log_correlationid = tn

    qtx = f"SELECT * FROM payment.transaction_getinfo(:tn)"
    rtx = BaseHelper.get_one(qtx, {"tn": tn})

    if rtx is not None:
        doc = rtx["document"]
        tname, merchant_id, amount_due = doc['tname'], doc["merchant_id"], doc["amount_due"]
        paid_date = dt_update = tools.current_utc()

        first_name, *last = buyer["name"].split()
        last_name = ' '.join(last)
        pl_customer = {
            "email": buyer["email"], "phone": buyer["phone"],
            "first_name": first_name, "last_name": last_name
        }
        customer_id = create_customer(buyer["email"], pl_customer)
        psp_reference = outcome_metadata["receipt_code"]

        ticket_md = {
            "merchant_code": psp_pos["code"],
            "merchant_terminal": psp_pos["terminal"],
            "date": paid_date.isoformat(),
            "receipt_code": psp_reference,
            "reference": tn,
            "amount": amount_due
        }
        dnotification = {"psp_id": psp_id, "updated_at": dt_update,
                         "psp_approval_code": approval_code, "masked_number": ldigits,
                         "buyer_fingerprint": json.dumps(buyer_fingerprint),
                         "buyer": json.dumps(buyer), "payment_method_id": 1,
                         "psp_reference": psp_reference, "psp_pos": json.dumps(psp_pos),
                         "paid_date": paid_date, "outcome_metadata": json.dumps(outcome_metadata),
                         "ticket_metadata": json.dumps(ticket_md), "customer_id": customer_id}

        if psp_code == 200:
            tx_status_id = constants.TX_PSP_APPROVED
            dnotification.update({"status_id": tx_status_id})

            # Task queue MKT Active Campaign
            payload_approved = {
                "merchant_id": merchant_id, "amount_due": amount_due}
            mkt_event_approved_transaction(payload_approved)
        else:
            tx_status_id = constants.TX_PSP_REJECTED
            dnotification.update({"status_id": tx_status_id})

        condicio = "ticket_number=:tn"
        qnotification = BaseHelper.generate_update_placeholder(
            f'payment.{tname}', dnotification.keys(), condicio)
        bparams_condicio = {"tn": tn}
        dnotification.update(bparams_condicio)
        r = BaseHelper.query(qnotification, dnotification)
        if r.rowcount > 0:
            # Creo un registro para el historial de la transaccion
            dtlog = {"merchant_id": merchant_id,
                     "status_id": tx_status_id, "ticket_number": tn}
            BaseHelper.query(BaseHelper.generate_insert_placeholder(
                'payment.transaction_log', dtlog.keys()), dtlog)

            dict_rst = {"code": 200, "message": "OK"}
        else:
            dict_rst = {"code": 500, "message": _MSG_ERR500}
    else:
        dict_rst = {"code": 404, "message": _MSG_ERR404}
    return jsonify(dict_rst)
