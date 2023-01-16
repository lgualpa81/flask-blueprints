from . import logdb_bp, jsonify, request, app, json
from application.model import db, BaseHelper
from application.helper import tools
from application.messages import _MSG_ERR500, _MSG_NOPARAMS


@logdb_bp.route("/logdb/psp", methods=["POST"])
def psp_log():
    _djson = request.get_json()

    if set(('ticket_number', "method", "tlapse", "req", "rsp_code", "rsp", "level")) == set(_djson):
        dlog = {"psp_id": 1, "trans_ticket_number": _djson["ticket_number"],
                "method": _djson["method"], "tlapse":float(_djson["tlapse"]), "level":_djson["level"],
                "req": json.dumps(_djson["req"]), "rsp_code": _djson["rsp_code"], "rsp": json.dumps(_djson["rsp"])}
        rlog = BaseHelper.query(BaseHelper.generate_insert_placeholder('payment.psp_log', dlog.keys()), dlog)
        if rlog.rowcount > 0:
            dict_rst = {"code": 200, "message": "OK"}
        else:
            dict_rst = {"code": 500, "message": _MSG_ERR500}
    else:
        dict_rst = {"code": 100, "message": _MSG_NOPARAMS}
    return jsonify(dict_rst)
