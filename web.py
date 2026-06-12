#!/usr/bin/env python3
"""Local website. Shares the core with the command line; streams downloads.

Run: python web.py [-p PORT]  (serves http://localhost:8086 by default). Run
directly, it reloads on source edits and stops cleanly on Ctrl-C.

The command line writes files to disk; the web streams them as attachments and
keeps nothing on the server. ``app`` is a plain WSGI callable, so a host like
PythonAnywhere imports it directly with no rewrite.
"""

import argparse
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
<p>The Bronica S2 series uses a helicoid separate from the camera.</p>
<p>The focusing scale is a thin metal strip, secured to the helicoid with three tiny screws.</p>
<p>The stock scale can combine up to four focal lengths on one scale, but there are only a few variations
of it, and it sucks for you if the lenses you use most don't appear on them.</p>
<p><b>This tool lets you pick one to three lens focal lengths (and your units between feet and meters).
It generates for you a strip with the scale(s) for those focal length(s), sized to be a perfect replacement
for the stock ones.</b></p>
<p>For printing to paper, there's a PDF output (with size calibration scale - make sure you're printing at
100% scale!).  I've found that paper glued to a brass strip and sealed with a sealer spray works pretty well.</p>
<p>However, if you'd rather go for an engraved metal one directly, there's also DXF output.</p>
<p>Use debug for a strip showing bare helicoid extension.</p>
<form method="post" action="/generate">
<table>
<tr><th>Unit</th><td>
  <label><input type="radio" name="unit" value="meters" checked> meters</label>
  <label><input type="radio" name="unit" value="feet"> feet</label>
</td></tr>
<tr><th>Focal lengths</th><td>
  <div class="focal"><select name="focal"><option value="">none</option>{_FOCAL_OPTIONS}</select> mm</div>
  <div class="focal"><select name="focal"><option value="">none</option>{_FOCAL_OPTIONS}</select> mm</div>
  <div class="focal"><select name="focal"><option value="">none</option>{_FOCAL_OPTIONS}</select> mm</div>
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
  <label><input type="checkbox" name="debug" value="1"> Include scale marked only with helicoid extension distances (useful for DIY lens design).  This debug strip is always in mm, and is the same regardless of focal length selection.</label>
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
    unit_value = request.forms.get("unit", "meters")
    focals = [int(v) for v in request.forms.getall("focal") if v]

    try:
        _validate(unit_value, focals, debug, fmt)
    except ValueError as exc:
        response.status = 400
        return f"<p>error: {exc}</p><p><a href='/'>back</a></p>"

    focal_model = build_model(Unit(unit_value), focals) if focals else None
    debug_model = build_model(None, [], debug=True) if debug else None
    if focals:
        dxf_base = f"{unit_value}_" + "_".join(str(f) for f in sorted(set(focals)))
        pdf_base = f"{dxf_base}_debug" if debug else dxf_base
    else:
        dxf_base, pdf_base = None, "debug"
    return _stream(focal_model, debug_model, fmt, page, pdf_base, dxf_base)


def _validate(unit_value, focals, debug, fmt):
    if not focals and not debug:
        raise ValueError("choose one to three focal lengths, or enable debug")
    if focals:
        if unit_value not in (u.value for u in Unit):
            raise ValueError("unknown unit")
        if len(set(focals)) > config.MAX_FOCAL_CHOICES:
            raise ValueError(f"at most {config.MAX_FOCAL_CHOICES} focal lengths")
        unknown = [f for f in focals if f not in config.FOCAL_LENGTHS_MM]
        if unknown:
            raise ValueError(f"unsupported focal length(s) {unknown}")
    elif fmt in ("dxf", "both"):
        raise ValueError("DXF needs a focal length; the debug strip is PDF only")


def _stream(focal_model, debug_model, fmt, page, pdf_base, dxf_base):
    # The PDF carries both strips; the DXF carries the focus strip only, so it
    # keeps the plain focus name without the debug suffix.
    strips = [m for m in (focal_model, debug_model) if m is not None]
    if fmt == "pdf":
        return _attach(render_pdf(strips, page=page), f"{pdf_base}.pdf", "application/pdf")
    if fmt == "dxf":
        return _attach(render_dxf(focal_model), f"{dxf_base}.dxf", "application/dxf")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{pdf_base}.pdf", render_pdf(strips, page=page))
        z.writestr(f"{dxf_base}.dxf", render_dxf(focal_model))
    return _attach(buf.getvalue(), f"{pdf_base}.zip", "application/zip")


def _attach(data, filename, content_type):
    response.content_type = content_type
    response.set_header("Content-Disposition", f'attachment; filename="{filename}"')
    return data


def _run_dev_server(port):
    """Serve locally in one process: clean Ctrl-C, and reload on code changes.

    Bottle's own reloader splits into a parent and child, and on Ctrl-C the two
    can race so a child is left holding the port. This runs the WSGI server in a
    single process. A signal handler stops it and closes the listening socket; a
    watcher thread re-execs the process when a source file changes, which closes
    that socket too (it is non-inheritable), so the new process binds cleanly.
    """
    import signal
    import sys
    import threading
    import time
    from wsgiref.simple_server import make_server

    import bottle
    bottle.debug(True)

    httpd = make_server("localhost", port, app)

    def reload_on_change():
        here = os.path.dirname(os.path.abspath(__file__))
        watched = {os.path.abspath(__file__)}
        for mod in list(sys.modules.values()):
            path = getattr(mod, "__file__", None)
            if path and os.path.abspath(path).startswith(here):
                watched.add(os.path.abspath(path))
        mtimes = {f: os.path.getmtime(f) for f in watched if os.path.exists(f)}
        while True:
            time.sleep(1.0)
            for f, t in mtimes.items():
                if os.path.exists(f) and os.path.getmtime(f) != t:
                    os.execv(sys.executable, [sys.executable, *sys.argv])

    def request_shutdown(*_):
        # shutdown() blocks until serve_forever returns, so call it off-thread.
        threading.Thread(target=httpd.shutdown, daemon=True).start()

    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)
    threading.Thread(target=reload_on_change, daemon=True).start()

    print(f"Serving on http://localhost:{port}/  (Ctrl-C to stop)", flush=True)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serve the focusing scale generator locally.")
    parser.add_argument("-p", "--port", type=int, default=8086, help="port to serve on")
    args = parser.parse_args()
    _run_dev_server(args.port)
