import base64
import math
from fpdf import FPDF, HTMLMixin
from . import tools
from flask import current_app as app


class PDF(FPDF, HTMLMixin):
    def __init__(self, orientation="portrait", unit="mm", format="A4", font_cache_dir=True):
        FPDF.__init__(self, orientation="portrait", unit="mm",
                      format="A4", font_cache_dir=True)

    def rotateText(self, angle, x=None, y=None):
        """
        This method allows to perform a rotation around a given center.
        The rotation affects all elements which are printed inside the indented context
        (with the exception of clickable areas).
        Args:
            angle (float): angle in degrees
            x (float): abscissa of the center of the rotation
            y (float): ordinate of the center of the rotation
        Notes
        -----
        Only the rendering is altered. The `get_x()` and `get_y()` methods are not
        affected, nor the automatic page break mechanism.
        """
        if x is None:
            x = self.x
        if y is None:
            y = self.y
        if angle == 0:
            self._out("Q\n")
        else:
            angle *= math.pi / 180
            c, s = math.cos(angle), math.sin(angle)
            cx, cy = x * self.k, (self.h - y) * self.k
            s = (
                f"q {c:.5F} {s:.5F} {-s:.5F} {c:.5F} {cx:.2F} {cy:.2F} cm "
                f"1 0 0 1 {-cx:.2F} {-cy:.2F} cm\n"
            )
            self._out(s)


class Voucher:

    def upload_bucket(self, raw_pdf, data):
        trans_id = data["trans_id"]
        merchant_id = data["merchant_id"]

        b64_file = base64.b64encode(raw_pdf).decode()

        _payload_upload = {"image_b64": b64_file, "image_name": f"voucher-{trans_id}.pdf",
                           "merchant_id": merchant_id, "directory": "pdf"}
        _r_upload = tools.call_endpoint(
            app.config["SVC_COMMERCE_UPLOAD_FILES_GCP"], _payload_upload)["resp_json"]
        file_bucket = ""
        if _r_upload["code"] == 200:
            file_bucket = _r_upload["file_url"]
        return file_bucket

    def generate_voucher(self, data):
        trans_id = data["trans_id"]
        merchant_id = data["merchant_id"]
        _x = 80.0
        _cw = 70
        _font_size = 11
        pdf = PDF()
        pdf.add_page()
        pdf.set_text_color(64, 63, 76)
        pdf.set_font('Helvetica', '', _font_size)
        pdf.image("https://storage.googleapis.com/commerce-files-bucket-prod/mobile/voucher-bg.png", 50,0, 120, 300)

        pdf.set_font('Helvetica', '', _font_size-1)
        pdf.set_xy(_x+13, 15.0)
        pdf.cell(_cw, 5, 'Movimiento hecho en', 0, ln=1)

        pdf.set_xy(_x+13, 50.0)
        pdf.cell(_cw, 5, 'Número de referencia', 0, ln=1)

        pdf.set_font('Helvetica', 'B', _font_size+6)
        pdf.set_xy(_x, 60.0)
        pdf.cell(_cw-10, 5, data["sku"], 0, ln=1, align='C')

        pdf.set_font('Helvetica', '', _font_size)
        pdf.set_xy(_x, 80.0)
        pdf.cell(_cw, 5, 'Código único', 0, ln=1)
        pdf.set_xy(_x, 85.0)
        pdf.set_font('Helvetica', 'B', _font_size)
        pdf.cell(_cw, 5, data["unique_code"], 0, ln=1)

        pdf.set_xy(_x, 95.0)
        pdf.set_font('Helvetica', '', _font_size)
        pdf.cell(_cw, 5, 'Terminal', 0, ln=1)
        pdf.set_xy(_x, 100.0)
        pdf.set_font('Helvetica', 'B', _font_size)
        pdf.cell(_cw, 5, data["terminal"], 0, ln=1)

        pdf.set_xy(_x, 110.0)
        pdf.set_font('Helvetica', '', _font_size)
        pdf.cell(_cw, 5, 'Número de transacción', 0, ln=1)
        pdf.set_xy(_x, 115.0)
        pdf.set_font('Helvetica', 'B', _font_size)
        pdf.cell(_cw, 5, '45454545', 0, ln=1)

        pdf.set_xy(_x, 125.0)
        pdf.set_font('Helvetica', '', _font_size)
        pdf.cell(_cw, 5, 'Fecha y hora de transacción', 0, ln=1)
        pdf.set_xy(_x, 130.0)
        pdf.set_font('Helvetica', 'B', _font_size)
        pdf.cell(_cw, 5, data["paid_date"], 0, ln=1)

        pdf.set_xy(_x, 140.0)
        pdf.set_font('Helvetica', '', _font_size)
        pdf.cell(_cw, 5, 'Moneda', 0, ln=1)
        pdf.set_xy(_x, 145.0)
        pdf.set_font('Helvetica', 'B', _font_size)
        pdf.cell(_cw, 5, data["currency"], 0, ln=1)

        pdf.set_xy(_x, 155.0)
        pdf.set_font('Helvetica', '', _font_size)
        pdf.cell(_cw, 5, 'Valor total', 0, ln=1)
        pdf.set_xy(_x, 160.0)
        pdf.set_font('Helvetica', 'B', _font_size)
        pdf.cell(_cw, 5, str(data["amount_paid"]), 0, ln=1)

        pdf.set_xy(_x, 170.0)
        pdf.set_font('Helvetica', '', _font_size)
        pdf.cell(_cw, 5, 'IVA', 0, ln=1)
        pdf.set_xy(_x, 175.0)
        pdf.set_font('Helvetica', 'B', _font_size)
        pdf.cell(_cw, 5, str(data["iva"]), 0, ln=1)

        pdf.set_xy(_x, 185.0)
        pdf.set_font('Helvetica', '', _font_size)
        pdf.cell(_cw, 5, 'Base devolución', 0, ln=1)
        pdf.set_xy(_x, 190.0)
        pdf.set_font('Helvetica', 'B', _font_size)
        pdf.cell(_cw, 5, str(data["taxable_income"]), 0, ln=1)

        pdf.set_xy(_x, 200.0)
        pdf.set_font('Helvetica', '', _font_size)
        pdf.cell(_cw, 5, 'Valor Neto', 0, ln=1)
        pdf.set_xy(_x, 205.0)
        pdf.set_font('Helvetica', 'B', _font_size)
        pdf.cell(_cw, 5, str(data["net_amount"]), 0, ln=1)

        pdf.set_xy(_x, 215.0)
        pdf.set_font('Helvetica', '', _font_size)
        pdf.cell(_cw, 5, 'Referencia', 0, ln=1)
        pdf.set_xy(_x, 220.0)
        pdf.set_font('Helvetica', 'B', _font_size)
        pdf.cell(_cw, 5, data["reference"], 0, ln=1)

        pdf.set_xy(_x, 230.0)
        pdf.set_font('Helvetica', '', _font_size)
        pdf.cell(_cw, 5, 'Descripción', 0, ln=1)
        pdf.set_xy(_x, 235.0)
        pdf.set_font('Helvetica', 'B', _font_size)
        pdf.cell(_cw, 5, data["description"], 0, ln=1)

        pdf.set_xy(_x, 245.0)
        pdf.set_font('Helvetica', '', _font_size)
        pdf.cell(_cw, 5, 'Estado de la transacción', 0, ln=1)
        pdf.set_xy(_x, 250.0)
        pdf.set_font('Helvetica', 'B', _font_size)
        pdf.cell(_cw, 5, data["status"], 0, ln=1)

        pdf.set_xy(_x, 260.0)
        pdf.set_font('Helvetica', '', _font_size)
        pdf.cell(_cw, 5, 'Respuesta', 0, ln=1)
        pdf.set_xy(_x, 265.0)
        pdf.set_font('Helvetica', 'B', _font_size)
        pdf.cell(_cw, 5, data["details"], 0, ln=1)

        raw_pdf = pdf.output(dest='S')
        return self.upload_bucket(raw_pdf, {"merchant_id": merchant_id, "trans_id": trans_id})

    def voucher_html(self, data):
        trans_id = data["trans_id"]
        merchant_id = data["merchant_id"]

        pdf = PDF()
        pdf.add_page()
        pdf.write_html("""
            <h1>Big title</h1>
            <section>
                <h2>Section title</h2>
                <p><b>Hello</b> world. <u>I am</u> <i>tired</i>.</p>
                <p><a href="https://github.com/PyFPDF/fpdf2">PyFPDF/fpdf2 GitHub repo</a></p>
                <p align="right">right aligned text</p>
                <p>i am a paragraph <br />in two parts.</p>
                <font color="#00ff00"><p>hello in green</p></font>
                <font size="7"><p>hello small</p></font>
                <font face="helvetica"><p>hello helvetica</p></font>
                <font face="times"><p>hello times</p></font>
            </section>
            <section>
                <h2>Other section title</h2>
                <ul><li>unordered</li><li>list</li><li>items</li></ul>
                <ol><li>ordered</li><li>list</li><li>items</li></ol>
                <br>
                <br>
                <pre>i am preformatted text.</pre>
                <pre>i am preformatted text 2.</pre>
                <br>
                <blockquote>hello blockquote</blockquote>
                <table width="50%">
                <thead>
                    <tr>
                    <th width="30%">ID</th>
                    <th width="70%">Name</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                    <td>1</td>
                    <td>Alice</td>
                    </tr>
                    <tr>
                    <td>2</td>
                    <td>Bob</td>
                    </tr>
                </tbody>
                </table>
            </section>
        """)
        raw_pdf = pdf.output(dest='S')
        return self.upload_bucket(raw_pdf, {"merchant_id": merchant_id, "trans_id": trans_id})
