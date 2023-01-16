from flask import request
import math


def request_pagination():
    if 'page' in request.args and 'limit' in request.args:
        page = abs(int(request.args["page"]))
        limit = abs(int(request.args["limit"]))
        offset = (limit * page) - limit  # do not put $limit*($page - 1)
        if (offset < 0):
            offset = 0
        if (limit > 500):
            limit = 10
    else:
        offset = 0
        limit = 10
        page = 1

    return {"offset": offset, "page": page, "limit": limit}


def build_pagination(qresult, page, limit):
    total_returned = len(qresult)
    rs = []
    if qresult is not None and total_returned > 0:
        total_records = qresult[0]["sql_count"]
        total_pages = math.ceil(
            total_records / limit) if total_records > 0 else 0

        if (page > total_pages):
            page = total_pages

        for r in qresult:
            del r["sql_count"]
            rs.append(r)
    else:
        total_records, total_pages = 0
    pagination = {"total_results": total_records, "total_pages": total_pages,
                  "total_returned": total_returned, "current_page": page}
    return {"data": rs, "pagination": pagination}
