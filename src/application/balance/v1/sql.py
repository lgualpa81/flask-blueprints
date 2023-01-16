from application.model import db, BaseHelper
import json


class Customer:
    @staticmethod
    def add_customer(kfield):
        return BaseHelper.query(BaseHelper.generate_insert_placeholder('public.customers', kfield.keys()), kfield)


class Balance:
    @staticmethod
    def get_regular_customers(_com_id):
        qrc = "SELECT c.id as customer_id, c.first_name as names, c.last_name as last_names, c.email, c.phone \
            FROM payment.view_merchant_transactions vtx INNER JOIN public.customers c on vtx.customer_id = c.id \
            WHERE merchant_id = :_p AND status_id in (14,15,16) \
                AND (to_char(paid_date, 'YYYY-MM') BETWEEN to_char(current_date - interval '3 month', 'YYYY-MM') AND to_char(current_date, 'YYYY-MM')) \
            GROUP BY 1,2,3,4 HAVING count(vtx.*)>=1"
        return BaseHelper.get_all(qrc, {"_p": _com_id})

    @staticmethod
    def get_transaction_activity_summary(_com_id, _usr_id, kpagination):
        offset, limit = kpagination["offset"], kpagination["limit"]
        cond = "AND vtx.user_id=:_p2" if _usr_id != 0 else ""

        q = f"SELECT vtx.ticket_number as trans_id, \
                to_char(public.utc2localtz(vtx.paid_date, 'america/bogota'), 'YYYY-MM-DD HH24:MI:SS') as paid_date, \
                vtx.amount_due as amount_paid, cy.code as currency, \
	            coalesce(c.id,0) as customer_id, coalesce(c.first_name,'') as customer_names, coalesce(c.last_name,'') as customer_last_names, \
                vtx.status_name as status, count(*) over() as sql_count \
            FROM payment.view_merchant_transactions vtx left join public.customers c on vtx.customer_id = c.id \
	            inner join public.currency cy on cy.id = vtx.currency_id \
            WHERE merchant_id = :_p1 and (vtx.status_id between 13 and 22) {cond} \
                and (to_char(paid_date, 'YYYY-MM') between to_char(current_date - interval '3 month', 'YYYY-MM') and to_char(current_date, 'YYYY-MM')) \
            ORDER BY 2 DESC OFFSET {offset} LIMIT {limit}"

        return BaseHelper.get_all(q, {"_p1": _com_id})

    @staticmethod
    def get_detail_transaction(_com_id, _transid):
        q = "SELECT vtx.ticket_number as trans_id, \
                to_char(public.utc2localtz(vtx.paid_date, 'america/bogota'), 'YYYY-MM-DD HH24:MI:SS') as paid_date, \
                vtx.amount_due, cy.code as currency, vtx.untaxed_amount, \
	            coalesce(c.id,0) as customer_id, coalesce(c.first_name,'') as customer_names, coalesce(c.last_name,'') as customer_last_names, \
                vtx.status_name as status, vtx.amount_detail, vtx.country_id, trim(vtx.psp_approval_code) as sku  \
            FROM payment.view_merchant_transactions vtx left join public.customers c on vtx.customer_id = c.id \
	            inner join public.currency cy on cy.id = vtx.currency_id \
            WHERE vtx.merchant_id = :_p1 AND vtx.ticket_number = :_p2"
        return BaseHelper.get_one(q, {"_p1": _com_id, "_p2": _transid})

    @staticmethod
    def get_voucher_detail(_com_id, _transid):
        q = "SELECT vtx.ticket_number as trans_id, \
                to_char(public.utc2localtz(vtx.paid_date, 'america/bogota'), 'YYYY-MM-DD HH24:MI:SS') as paid_date, \
                vtx.amount_due as amount_paid, cy.code as currency, vtx.untaxed_amount, \
	            coalesce(c.id,0) as customer_id, coalesce(c.first_name,'') as customer_names, coalesce(c.last_name,'') as customer_last_names, \
                vtx.status_name as status, vtx.amount_detail, coalesce(vtx.psp_pos, '{}') as psp_pos, \
                vtx.description, coalesce(vtx.outcome_metadata, '{}') as outcome_metadata, \
                vtx.country_id, trim(vtx.psp_approval_code) as sku, coalesce(vtx.psp_reference, '') as psp_reference \
            FROM payment.view_merchant_transactions vtx left join public.customers c on vtx.customer_id = c.id \
	            inner join public.currency cy on cy.id = vtx.currency_id \
            WHERE vtx.merchant_id = :_p1 AND vtx.ticket_number = :_p2"
        return BaseHelper.get_one(q, {"_p1": _com_id, "_p2": _transid})

    @staticmethod
    def get_transaction_latest_approved(_com_id, _usr_id, kpagination):
        offset, limit = kpagination["offset"], kpagination["limit"]
        cond = "AND vtx.user_id=:_p2" if _usr_id != 0 else ""

        q = f"SELECT vtx.ticket_number as trans_id, \
                to_char(public.utc2localtz(vtx.paid_date, 'america/bogota'), 'YYYY-MM-DD HH24:MI:SS') as paid_date, \
                vtx.amount_due as amount_paid, cy.code as currency, \
	            coalesce(c.id, 0) as customer_id, coalesce(c.first_name,'') as customer_names, coalesce(c.last_name,'') as customer_last_names, \
                vtx.status_name as status, count(*) over() as sql_count \
            FROM payment.view_merchant_transactions vtx left join public.customers c on vtx.customer_id = c.id \
	            inner join public.currency cy on cy.id = vtx.currency_id \
            WHERE merchant_id = :_p1 and vtx.status_id=14 {cond} \
                and (to_char(paid_date, 'YYYY-MM') between to_char(current_date - interval '3 month', 'YYYY-MM') and to_char(current_date, 'YYYY-MM')) \
            ORDER BY 2 DESC OFFSET {offset} LIMIT {limit}"

        return BaseHelper.get_all(q, {"_p1": _com_id, "_p2": _usr_id})

    @staticmethod
    def get_transaction_latest_payout(_com_id, _usr_id, kpagination):
        offset, limit = kpagination["offset"], kpagination["limit"]
        cond = "AND vtx.user_id=:_p2" if _usr_id != 0 else ""
        settle_status = 16

        q = f"SELECT vtx.ticket_number as trans_id, \
                vtx.amount_due as amount_paid, cy.code as currency, \
                coalesce((vtx.amount_detail->>'monto_depositar')::numeric,0) as amount_payable, \
                coalesce(c.id, 0) as customer_id, coalesce(c.first_name,'') as customer_names, coalesce(c.last_name,'') as customer_last_names, \
                (SELECT to_char(public.utc2localtz(created_at, 'america/bogota'), 'YYYY-MM-DD HH24:MI:SS') from payment.transaction_log tlog \
                where tlog.ticket_number = vtx.ticket_number and status_id = {settle_status}) as payout_date, \
                vtx.status_name as status, count(*) over() as sql_count \
            FROM payment.view_merchant_transactions vtx left join public.customers c on vtx.customer_id=c.id \
                inner join public.currency cy on cy.id=vtx.currency_id \
            WHERE vtx.merchant_id=:_p1 and vtx.status_id={settle_status} {cond} \
                and (to_char(paid_date, 'YYYY-MM') between to_char(current_date - interval '3 month', 'YYYY-MM') and to_char(current_date, 'YYYY-MM')) \
            ORDER BY 2 DESC OFFSET {offset} LIMIT {limit}"

        return BaseHelper.get_all(q, {"_p1": _com_id, "_p2": _usr_id})

    @staticmethod
    def get_balance_daily(_com_id, _user_id):
        cond = "AND vtx.user_id=:_p2" if _user_id != 0 else ""

        q = f"SELECT sum(a.payout_amount) as total, \
                json_agg(json_build_object('date', a.paid_date, 'amount', a.payout_amount ) ORDER BY a.paid_date) as transactions \
            FROM (select date(public.utc2localtz(paid_date, 'america/bogota')) as paid_date, \
                    sum((amount_detail->>'monto_depositar')::numeric) as payout_amount \
                from payment.view_merchant_transactions vtx \
                where status_id in (16) AND merchant_id=:_p1 {cond} \
                    AND (date(paid_date) between date(current_date - interval '1 month') and current_date) \
                group by 1 ) as a;"
        return BaseHelper.get_one(q, {"_p1": _com_id, "_p2": _user_id})

    @staticmethod
    def get_balance_monthly(_com_id, _user_id):
        cond = "AND user_id=:_p2" if _user_id != 0 else ""

        q = f"SELECT to_char(a.paid_date, 'YYYY-MM') as month, sum(a.payout_amount) as total, \
                json_agg(json_build_object('day', extract(day from a.paid_date), 'amount', a.payout_amount ) ORDER BY a.paid_date) as transactions \
            FROM ( select date(public.utc2localtz(paid_date, 'america/bogota')) as paid_date, \
                    sum((amount_detail->>'monto_depositar')::numeric) as payout_amount \
                from payment.view_merchant_transactions \
                where status_id in (16) AND merchant_id=:_p1 {cond} \
                    and (date(paid_date) between date(current_date - interval '3 month') and current_date) \
                group by 1 ) as a \
            GROUP BY 1 ORDER BY 1 ASC"
        return BaseHelper.get_all(q, {"_p1": _com_id, "_p2": _user_id})

    @staticmethod
    def get_balance_yearly(_com_id, _user_id):
        cond = "AND user_id=:_p2" if _user_id != 0 else ""

        q = f"SELECT sum(a.payout_amount) as total, json_agg(json_build_object('year', a.paid_date, 'amount', a.payout_amount ) ORDER BY a.paid_date) as transactions \
            FROM ( select extract(year from paid_date) as paid_date, sum((amount_detail->>'monto_depositar')::numeric) as payout_amount \
                from payment.view_merchant_transactions \
                where status_id in (16) AND merchant_id=:_p1 {cond} \
                    and (date(paid_date) between date(current_date - interval '1 year') and current_date) \
                group by 1 ) as a;"
        return BaseHelper.get_one(q, {"_p1": _com_id, "_p2": _user_id})

    @staticmethod
    def get_payable_balance(_com_id, _usr_id):
        if _usr_id == 0:
            qbl = "SELECT payment.merchant_saldo_acreditar(:_p1) as saldo"
        else:
            qbl = "SELECT payment.merchant_saldo_acreditar_usuario(:_p1, :_p2) as saldo"
        return BaseHelper.get_one(qbl, {"_p1": _com_id, "_p2": _usr_id})

    @staticmethod
    def get_payable_total_transactions(_com_id, _usr_id):
        cond = "AND user_id=:_p2" if _usr_id != 0 else ""
        qbl = f"SELECT count(*) as total  \
                FROM payment.view_merchant_transactions where merchant_id = :_p1 and status_id = 15 {cond};"
        return BaseHelper.get_one(qbl, {"_p1": _com_id, "_p2": _usr_id})

    @staticmethod
    def get_approved_balance(_com_id, _usr_id):
        cond = "AND user_id=:_p2" if _usr_id != 0 else ""
        q = f"SELECT coalesce(sum((amount_detail->>'monto_depositar')::numeric),0) as saldo \
            FROM payment.view_merchant_transactions where merchant_id = :_p1 and status_id = 14 {cond};"
        return BaseHelper.get_one(q, {"_p1": _com_id})

    @staticmethod
    def get_payable_order(_com_id, _usr_id, _code):
        if _usr_id == 0:
            q = "SELECT payment.merchant_payable_order(:_p1, :_p2) as code"
        else:
            q = "SELECT payment.dataphone_payable_order(:_p1, :_p2, :_p3) as code"
        return BaseHelper.get_one(q, {"_p1": _com_id, "_p2": _code, "_p3": _usr_id})

    @staticmethod
    def get_payable_activity(_com_id, _usr_id, kpagination):
        offset, limit = kpagination["offset"], kpagination["limit"]
        cond = "AND vtx.user_id=:_p2" if _usr_id != 0 else ""

        q = f"SELECT vtx.ticket_number as trans_id, \
                vtx.amount_due as amount_paid, cy.code as currency, \
                coalesce((vtx.amount_detail->>'monto_depositar')::numeric,0) as amount_payable, \
                coalesce(c.id, 0) as customer_id, coalesce(c.first_name,'') as customer_names, coalesce(c.last_name,'') as customer_last_names, \
                vtx.status_name as status, count(*) over() as sql_count \
            FROM payment.view_merchant_transactions vtx left join public.customers c on vtx.customer_id=c.id \
                inner join public.currency cy on cy.id=vtx.currency_id \
            WHERE vtx.merchant_id=:_p1 and vtx.status_id=15 {cond} \
            ORDER BY 2 DESC OFFSET {offset} LIMIT {limit}"
        return BaseHelper.get_all(q, {"_p1": _com_id})
