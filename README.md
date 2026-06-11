# Bronica S2 focusing scale generator

Generate focusing scale strips for the Bronica S2 helicoid. Pick a unit and one
to three focal lengths; get a print-ready PDF and/or a laser-ready DXF.

The focal lengths offered: 40, 45, 50, 75, 80, 85, 100, 105, 135, 150, 200.

Unlike the stock strip that holds two rows each with two colors (white and red), this
generator will produce up to three rows in a single color.

## Output

The PDF includess a 1 cm and a 1 inch reference line (you must change print size to 100%; not the default fit-to-page).  Check them with a ruler before trusting the strip. 

The DXF carries the outline and slots on a `CUT` layer and the dots and text on an
`ENGRAVE` layer.


## Setup

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Command line

Writes named files into an output directory.

```
.venv/bin/python cli.py --unit meters --focal 75 --focal 150 --format both --out ./out
.venv/bin/python cli.py --unit feet --focal 100 --format pdf
.venv/bin/python cli.py --debug --format dxf
```

Options: `--unit feet|meters`, `--focal` (repeat up to three), `--format
pdf|dxf|both`, `--out`, `--page letter|a4`, `--debug` for the bare extension
strip.

## Website

```
.venv/bin/python web.py
```

Serves a form at http://localhost:8080 and streams the result as a download.


