from . import backoffice_bp, jsonify, request, app, json, constants
from application.model import db, BaseHelper
from application.helper import tools
from application.messages import _MSG_ERR404, _MSG_ERR500, _MSG_NOPARAMS, _MSG_PAYLINK01, _MSG_PAYLINK02, _MSG_PAYLINK03, _MSG_BCKOFC01
from application.helper.decorator import jwt_optional_custom, jwt_required_custom


@backoffice_bp.route("/backoffice/commerce/signup-payment-profile", methods=["POST"])
@jwt_optional_custom
def signup_payment_profile():
    _djson = request.get_json()
    if set(('vat_rate', 'taxpayer_type', 'country_id', 'agreement', 'merchant_id')) == set(_djson):
        vat_rate = int(_djson["vat_rate"])
        jp = True if int(_djson["taxpayer_type"]) != 1 else False
        country_id = int(_djson["country_id"])
        agreement = int(_djson["agreement"])
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


@backoffice_bp.route("/backoffice/commerce/signup-payment-profile-v2", methods=["POST"])
@jwt_optional_custom
def signup_payment_profile_v2():
    _djson = request.get_json()
    if set(('taxpayer_type', 'country_id', 'agreement', 'merchant_id')) == set(_djson):
        jp = True if int(_djson["taxpayer_type"]) != 1 else False
        country_id = int(_djson["country_id"])
        agreement = int(_djson["agreement"])
        merchant_id = int(_djson["merchant_id"])

        qch_method = "SELECT id, code, name FROM payment.charging_mode WHERE active=true AND juridical_person=:jp \
            AND agreement_id=:ag AND country_id=:country_id"
        rch_method = BaseHelper.get_one(
            qch_method, {"jp": jp, "ag": agreement, "country_id": country_id})
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


@backoffice_bp.route("/backoffice/dashboard/transaction-tracking/filters", methods=["GET"])
@jwt_optional_custom
def get_transaction_setup():
    qagreement = "SELECT id, name FROM payment.agreement WHERE active=true ORDER BY 1"
    ragreement = BaseHelper.get_all(qagreement)

    tx_status = "SELECT id, status_name as status FROM payment.status \
        WHERE active=true AND table_name='transaction_x' ORDER BY 1"
    rtx_status = BaseHelper.get_all(tx_status)

    dict_rst = {"code": 200, "message": "OK", "data": {
        "agreement": ragreement, "status": rtx_status}}
    return jsonify(dict_rst)


@backoffice_bp.route("/backoffice/dashboard/transaction-tracking", methods=["POST"])
@jwt_required_custom
def get_transaction_tracking():
    _djson = request.get_json()
    if set(('agreement_id', 'status_id', 'start_date', 'end_date')) == set(_djson):
        start_date = _djson["start_date"]
        end_date = _djson["end_date"]
        tx_status_id = _djson["status_id"]
        agreement_id = _djson["agreement_id"]

        filters = ""
        if tx_status_id:
            filters += "AND status_id=:p1 "
        if agreement_id:
            filters += "AND agreement_id=:p2 "
        if start_date and end_date:
            filters += "AND (date(public.utc2localtz(tx_created_at, 'america/bogota')) between :d_ini and :d_end) "

        qtx = f"select ticket_number, fingerprint, com_id, com_name, com_address, com_phone, \
                public.utc2localtz(com_date_joined, 'america/bogota') as com_date_joined, \
                com_email, com_taxpayer_code, com_taxpayer, \
                charging_mode, agreement, amount_due, tax, amount_detail, psp_approval_code as approval_code, \
                cost_buyer, paid_date, status, description, \
                public.utc2localtz(tx_created_at, 'america/bogota') as tx_created_at, \
                public.utc2localtz(tx_updated_at, 'america/bogota') as tx_updated_at, country, currency, \
                usr_id, usr_email, usr_fname, usr_lname, com_bank_account  \
            from ( select * from payment.view_dashboard_transactions where 1=1 {filters}) as t order by tx_created_at desc"
        rtx = BaseHelper.get_all(
            qtx, {"p1": tx_status_id, "p2": agreement_id, "d_ini": start_date, "d_end": end_date})
        if rtx is not None and len(rtx) > 0:
            dict_rst = {"code": 200, "message": "OK", "data": rtx}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@backoffice_bp.route("/backoffice/dashboard/transaction-tracking/commerce/<int:merchant_id>", methods=["POST"])
@jwt_required_custom
def get_transaction_tracking_commerce(merchant_id):
    _djson = request.get_json()
    if isinstance(merchant_id, int) and set(('agreement_id', 'status_id', 'start_date', 'end_date')) == set(_djson):
        start_date = _djson["start_date"]
        end_date = _djson["end_date"]
        tx_status_id = _djson["status_id"]
        agreement_id = _djson["agreement_id"]

        filters = ""
        if tx_status_id:
            filters += "AND status_id=:p1 "
        if agreement_id:
            filters += "AND agreement_id=:p2 "
        if start_date and end_date:
            filters += "AND (date(public.utc2localtz(tx_created_at, 'america/bogota')) between :d_ini and :d_end) "

        qtx = f"select ticket_number, fingerprint, com_id, com_name, com_address, com_phone, \
                public.utc2localtz(com_date_joined, 'america/bogota') as com_date_joined, \
                com_email, com_taxpayer_code, com_taxpayer, \
                charging_mode, agreement, amount_due, tax, amount_detail, psp_approval_code as approval_code, \
                cost_buyer, paid_date, status, description, \
                public.utc2localtz(tx_created_at, 'america/bogota') as tx_created_at, \
                public.utc2localtz(tx_updated_at, 'america/bogota') as tx_updated_at, country, currency, \
                usr_id, usr_email, usr_fname, usr_lname, com_bank_account  \
            from ( select * from payment.view_dashboard_transactions where com_id=:p0 {filters}) as t order by tx_created_at desc"
        rtx = BaseHelper.get_all(qtx, {"p0": merchant_id, "p1": tx_status_id,
                                       "p2": agreement_id, "d_ini": start_date, "d_end": end_date})
        if rtx is not None and len(rtx) > 0:
            dict_rst = {"code": 200, "message": "OK", "data": rtx}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@backoffice_bp.route("/backoffice/dashboard/payments-statistics", methods=["POST"])
@jwt_required_custom
def get_payments_statistics():
    _djson = request.get_json()
    if set(('merchant_id', 'start_date', 'end_date')) == set(_djson):
        start_date = _djson["start_date"]
        end_date = _djson["end_date"]
        merchant_id = _djson["merchant_id"]

        filters = ""
        if merchant_id:
            filters += "AND com_id=:p0 "
        if start_date and end_date:
            filters += "AND (date(public.utc2localtz(created_at, 'america/bogota')) between :d_ini and :d_end) "

        qtx = f"select count(*) as total_trans, coalesce(sum(amount_due),0) as total_amount, \
                    count(*) FILTER (WHERE status_id =9) AS total_created, \
                    coalesce(sum(case when status_id =9 then amount_due else 0 end),0) as created_amount, \
                    count(*) FILTER (WHERE status_id not in (9,14,16,17,18)) AS total_declined, \
                    coalesce(sum(case when status_id not in (9,14,16,17,18) then amount_due else 0 end),0) as declined_amount, \
                    count(*) FILTER (WHERE status_id =14) AS total_approved, \
                    coalesce(sum(case when status_id=14 then amount_due else 0 end), 0) as approved_amount, \
                    count(*) FILTER (WHERE status_id=16) AS total_accredited, \
                    coalesce(sum(case when status_id = 16 then amount_due else 0 end),0) as accredited_amount \
                from payment.view_dashboard_payments_statistics_backoffice where 1=1 {filters};"

        rtx = BaseHelper.get_one(
            qtx, {"p0": merchant_id, "d_ini": start_date, "d_end": end_date})
        if rtx is not None:
            dict_rst = {"code": 200, "message": "OK", "data": rtx}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@backoffice_bp.route("/backoffice/dashboard/commerce/latest-transactions", methods=["POST"])
@jwt_required_custom
def get_latest_transactions():
    _djson = request.get_json()
    if 'merchant_id' in _djson:
        merchant_id = _djson["merchant_id"]
        filters = ""
        if merchant_id:
            filters += "AND com_id=:p0 "

        limit = request.args['limit'] if 'limit' in request.args and isinstance(
            request.args.get('limit', type=int), int) else 10

        qtx = f"SELECT ticket_number, com_name, amount_due, status, coalesce(last_numbers, '') as last_numbers, \
                public.utc2localtz(tx_created_at, 'america/bogota') as created_at, country, currency \
            FROM payment.view_dashboard_transactions \
            WHERE status_id not in (9,15,16,17,18) {filters} \
            ORDER BY created_at desc LIMIT {limit};"

        rtx = BaseHelper.get_all(qtx, {"p0": merchant_id})
        if rtx is not None and len(rtx) > 0:
            dict_rst = {"code": 200, "message": "OK", "data": rtx}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@backoffice_bp.route("/backoffice/control/sales-settlement", methods=["POST"])
@jwt_required_custom
def get_sales_settlement():
    _djson = request.get_json()
    if set(('status_id', 'start_date', 'end_date')) == set(_djson):
        start_date = _djson["start_date"]
        end_date = _djson["end_date"]
        status_id = _djson["status_id"]

        filters = ""
        if start_date and end_date:
            filters += "AND (date(public.utc2localtz(tx_created_at, 'america/bogota')) between :d_ini and :d_end) "

        filters += "AND status_id=:s1 " if status_id else "AND status_id not in (9,10,11,12,13) "

        qtx = f"select ticket_number, ( json_build_object('name', com_name, 'email', com_email, 'address', coalesce(com_address, ''),  \
                        'member', coalesce(usr_fname ||  ' ' || usr_lname, ''), 'phone', coalesce(com_phone, ''), \
                        'member_doc', coalesce(usr_doc_number, ''), 'date_joined', to_char(public.utc2localtz(com_date_joined, 'america/bogota'),'YYYY-MM-DD HH24:MI:SS'), \
                        'taxpayer', coalesce(com_taxpayer, ''), 'charging_mode', charging_mode, 'agreement', agreement)) as commerce,	\
                ( select json_agg(json_build_object('doc',dt.name, 'number', coalesce(td.document_number, ''), 'status', doc_st.status_name, \
                    'verified', case when td.verified then 'SI' else 'NO' end)) \
                  from commerce.tax_document td inner join commerce.status doc_st on doc_st.id = td.status_id \
                    inner join public.document_type dt on dt.id=td.document_type_id where t.com_id=td.merchant_id ) as com_docs, \
                com_bank_account, amount_due as amount_due, tax, amount_detail, psp_approval_code as approval_code, \
                cost_buyer, paid_date, status, coalesce(description, '') as trans_description, country, currency, \
                public.utc2localtz(tx_created_at, 'america/bogota') as trans_created_at, case when status_id not in (15,16,17,18,19,20,21,22) then 0 else 1 end as settle  \
            from (select * from payment.view_dashboard_transactions where 1=1 {filters} ) as t \
            order by trans_created_at desc;"

        rtx = BaseHelper.get_all(
            qtx, {"d_ini": start_date, "d_end": end_date, "s1": status_id})
        if rtx is not None and len(rtx) > 0:
            dict_rst = {"code": 200, "message": "OK", "data": rtx}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@backoffice_bp.route("/backoffice/control/settle-transaction", methods=["PUT"])
@jwt_required_custom
def transaction_settlement():
    _djson = request.get_json()
    if set(('ticket_number', 'status_id', 'notes', 'sys_user_id')) == set(_djson):
        tn = _djson["ticket_number"]
        settle_status = _djson["status_id"]
        settle_notes = _djson["notes"]
        sys_user_id = _djson["sys_user_id"]

        qtx = "SELECT * FROM payment.transaction_getinfo(:tn)"
        rtx = BaseHelper.get_one(qtx, {"tn": tn})

        if rtx is not None:
            doc = rtx["document"]
            tname, trans_status_id, trans_status = (
                doc["tname"], doc["status_id"], doc["status"])
            # status_id: 14->Pago aprobado por banco
            if trans_status_id == 14:
                qupd = "SELECT * FROM payment.transaction_settlement(:tn, ':st_id', :tname, :tnotes, ':tagent')"
                rupd = BaseHelper.query(qupd, {
                                        "tn": tn, "st_id": settle_status, "tname": tname, "tnotes": settle_notes, "tagent": sys_user_id})

                if rupd.rowcount > 0:
                    dict_rst = {"code": 200, "message": "OK"}
                else:
                    dict_rst = {"code": 500, "message": _MSG_ERR500}
            else:
                dict_rst = {"code": 300, "message": trans_status}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@backoffice_bp.route("/backoffice/control/commerce/latest-joined", methods=["POST"])
@jwt_required_custom
def get_latest_joins():
    _djson = request.get_json()
    if set(('start_date', 'end_date')) == set(_djson):
        start_date = _djson["start_date"]
        end_date = _djson["end_date"]

        filters = ""
        if start_date and end_date:
            filters += "AND (date(com_date_joined) between :d_ini and :d_end) "

        qjoins = f"select * from payment.view_control_commerce_joined WHERE 1=1 {filters}"
        rjoins = BaseHelper.get_all(
            qjoins, {"d_ini": start_date, "d_end": end_date})
        if rjoins is not None and len(rjoins) > 0:
            dict_rst = {"code": 200, "message": "OK", "data": rjoins}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)


@backoffice_bp.route("/backoffice/dashboard/void-transaction", methods=["DELETE"])
@jwt_required_custom
def void_transaction():
    _djson = request.get_json()
    if set(('sys_userid', 'tn', 'notes')) == set(_djson):
        tn, sys_userid = str(_djson["tn"]), _djson["sys_userid"]
        notes = _djson["notes"]

        qtx = "SELECT * FROM payment.transaction_getinfo(:tn)"
        rtx = BaseHelper.get_one(qtx, {"tn": tn})

        if rtx is not None:
            doc = rtx["document"]
            tname, trans_status_id = doc["tname"], doc["status_id"]
            trans_status = doc["status"]
            paid_date = tools.isoformat2str(
                doc["paid_dt_tz"], format='%Y-%m-%d')
            # status_id: 14->Pago aprobado por banco
            if trans_status_id == 14:
                qvoid = f"SELECT outcome_metadata, payment_method_id FROM payment.{tname} WHERE ticket_number=:tn"
                rvoid = BaseHelper.get_one(qvoid, {"tn": tn})
                payment_methodid = rvoid["payment_method_id"]
                if payment_methodid == 1:
                    void = rvoid["outcome_metadata"]
                    _payload = {"receipt_number": void["receipt_code"],
                                "tn": tn, 'paid_date': paid_date}
                    extra = {"http_method": "DELETE"}
                    _url = app.config["URL_PAYMENT_CARD_VOID"]
                    r_psp = tools.call_endpoint(
                        _url, _payload, **extra)["resp_json"]

                    _code_void = str(r_psp["code"])
                    # 20: anulacion exitosa, 21: Reclamo, 22: Reverso manual
                    settle_list = {'200': 20, '120': 21}
                    settle_status = settle_list[_code_void] if _code_void in settle_list.keys(
                    ) else 22

                    qupd = "SELECT * FROM payment.transaction_settlement(:tn, ':st_id', :tname, :tnotes, ':tagent')"
                    params_upd = {"tn": tn, "st_id": settle_status,
                                  "tname": tname, "tnotes": notes,
                                  "tagent": sys_userid}
                    rupd = BaseHelper.query(qupd, params_upd)

                    if rupd.rowcount > 0:
                        dict_rst = {"code": 200, "message": "OK"}
                    else:
                        dict_rst = {"code": 500, "message": _MSG_ERR500}
                else:
                    dict_rst = {
                        "code": 110, "message": "La anulación no esta habilitado para este método de pago"}
            else:
                dict_rst = {"code": 300, "message": trans_status}
        else:
            dict_rst = {"code": 404, "message": _MSG_ERR404}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)
