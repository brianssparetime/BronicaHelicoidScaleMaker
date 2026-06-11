#!/usr/bin/env python3
"""Local website. Shares the core with the command line; streams downloads.

Run: python web.py  (serves http://localhost:8080)

The command line writes files to disk; the web streams them as attachments and
keeps nothing on the server. ``app`` is a plain WSGI callable, so a host like
PythonAnywhere imports it directly with no rewrite.
"""

import io
import os
import zipfile

from bottle import Bottle, request, response, static_file

from scale_strip import config
from scale_strip.model import build_model
from scale_strip.render_dxf import render_dxf
from scale_strip.render_pdf import render_pdf
from scale_strip.units import Unit

app = Bottle()

_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

_FOCAL_OPTIONS = "".join(
    f'<option value="{f}">{f}</option>' for f in config.FOCAL_LENGTHS_MM
)


def _page():
    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>Bronica S2 focusing scale generator</title>
<link rel="stylesheet" href="/static/style.css">
</head><body>
<h1>Bronica S2 focusing scale generator</h1>
<p>Pick a unit and one to three focal lengths. Use debug for the bare extension strip.</p>
<form method="post" action="/generate">
<table>
<tr><th>Unit</th><td>
  <label><input type="radio" name="unit" value="meters" checked> meters</label>
  <label><input type="radio" name="unit" value="feet"> feet</label>
</td></tr>
<tr><th>Focal lengths</th><td>
  <select name="focal"><option value="">none</option>{_FOCAL_OPTIONS}</select>
  <select name="focal"><option value="">none</option>{_FOCAL_OPTIONS}</select>
  <select name="focal"><option value="">none</option>{_FOCAL_OPTIONS}</select>
  <span class="hint">mm</span>
</td></tr>
<tr><th>Format</th><td>
  <label><input type="radio" name="format" value="pdf" checked> PDF</label>
  <label><input type="radio" name="format" value="dxf"> DXF</label>
  <label><input type="radio" name="format" value="both"> both (zip)</label>
</td></tr>
<tr><th>Page</th><td>
  <label><input type="radio" name="page" value="letter" checked> Letter</label>
  <label><input type="radio" name="page" value="a4"> A4</label>
</td></tr>
<tr><th>Debug</th><td>
  <label><input type="checkbox" name="debug" value="1"> extension strip (ignores unit and focal lengths)</label>
</td></tr>
</table>
<p><button type="submit">Generate</button></p>
</form>
</body></html>"""


@app.get("/")
def index():
    return _page()


@app.get("/static/<name>")
def static(name):
    return static_file(name, root=_STATIC_DIR)


@app.post("/generate")
def generate():
    debug = request.forms.get("debug") == "1"
    fmt = request.forms.get("format", "pdf")
    page = request.forms.get("page", "letter")

    if debug:
        model = build_model(None, [], debug=True)
        base = "debug"
    else:
        unit_value = request.forms.get("unit", "meters")
        focals = [int(v) for v in request.forms.getall("focal") if v]
        try:
            _validate(unit_value, focals)
        except ValueError as exc:
            response.status = 400
            return f"<p>error: {exc}</p><p><a href='/'>back</a></p>"
        model = build_model(Unit(unit_value), focals)
        base = f"{unit_value}_" + "_".join(str(f) for f in sorted(set(focals)))

    return _stream(model, fmt, page, base)


def _validate(unit_value, focals):
    if unit_value not in (u.value for u in Unit):
        raise ValueError("unknown unit")
    if not focals:
        raise ValueError("choose one to three focal lengths")
    if len(set(focals)) > config.MAX_FOCAL_CHOICES:
        raise ValueError(f"at most {config.MAX_FOCAL_CHOICES} focal lengths")
    unknown = [f for f in focals if f not in config.FOCAL_LENGTHS_MM]
    if unknown:
        raise ValueError(f"unsupported focal length(s) {unknown}")


def _stream(model, fmt, page, base):
    if fmt == "pdf":
        return _attach(render_pdf(model, page=page), f"{base}.pdf", "application/pdf")
    if fmt == "dxf":
        return _attach(render_dxf(model), f"{base}.dxf", "application/dxf")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{base}.pdf", render_pdf(model, page=page))
        z.writestr(f"{base}.dxf", render_dxf(model))
    return _attach(buf.getvalue(), f"{base}.zip", "application/zip")


def _attach(data, filename, content_type):
    response.content_type = content_type
    response.set_header("Content-Disposition", f'attachment; filename="{filename}"')
    return data


if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True, reloader=True)
