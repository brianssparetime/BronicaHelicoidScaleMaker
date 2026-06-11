#!/usr/bin/env python3
"""Command line generator. Writes named files into an output directory.

    python cli.py --unit meters --focal 75 --focal 150 --format both --out ./out
    python cli.py --debug --format pdf
"""

import argparse
import sys
from pathlib import Path

from scale_strip import config
from scale_strip.model import build_model
from scale_strip.render_dxf import render_dxf
from scale_strip.render_pdf import render_pdf
from scale_strip.units import Unit


def _parse_args(argv):
    p = argparse.ArgumentParser(description="Generate a Bronica S2 focusing scale strip.")
    p.add_argument("--unit", choices=[u.value for u in Unit])
    p.add_argument("--focal", action="append", type=int, default=[], metavar="MM",
                   help="focal length in mm; repeat up to three times")
    p.add_argument("--format", choices=["pdf", "dxf", "both"], default="both")
    p.add_argument("--out", default="./out", help="output directory")
    p.add_argument("--page", choices=["letter", "a4"], default="letter")
    p.add_argument("--debug", action="store_true",
                   help="produce the extension strip instead of focus scales")
    return p.parse_args(argv)


def _validate(args):
    if args.debug:
        return
    if args.unit is None:
        raise SystemExit("error: --unit is required unless --debug")
    if not args.focal:
        raise SystemExit("error: give one to three --focal values, or use --debug")
    if len(args.focal) > config.MAX_FOCAL_CHOICES:
        raise SystemExit(f"error: at most {config.MAX_FOCAL_CHOICES} focal lengths")
    unknown = [f for f in args.focal if f not in config.FOCAL_LENGTHS_MM]
    if unknown:
        allowed = ", ".join(str(f) for f in config.FOCAL_LENGTHS_MM)
        raise SystemExit(f"error: unsupported focal length(s) {unknown}; choose from {allowed}")


def _basename(args):
    if args.debug:
        return "debug"
    focals = "_".join(str(f) for f in sorted(set(args.focal)))
    return f"{args.unit}_{focals}"


def main(argv=None):
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    _validate(args)

    unit = None if args.debug else Unit(args.unit)
    model = build_model(unit, args.focal, debug=args.debug)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    base = _basename(args)
    written = []
    if args.format in ("pdf", "both"):
        path = out / f"{base}.pdf"
        path.write_bytes(render_pdf(model, page=args.page))
        written.append(path)
    if args.format in ("dxf", "both"):
        path = out / f"{base}.dxf"
        path.write_bytes(render_dxf(model))
        written.append(path)

    for path in written:
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
