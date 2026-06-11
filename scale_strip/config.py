"""Physical constants of the helicoid and strip, and the offered focal lengths.

Constants are tagged where they come from. "firm" values are known from the
helicoid spec, "caliper" from measuring the part, "measured" from reading the
stock strip against a ruler, and "provisional" are estimates that want a caliper
pass. The provisional values affect where infinity and the central slot land,
not the internal correctness of any scale, and they are isolated here so a later
correction is a one-line edit. See design_docs/generator_math.md for the basis.
"""

# Helicoid travel.
EXT_MAX_MM = 14.0      # extension from infinity to minimum focus   (firm)
ROT_DEG = 250.0        # helicoid rotation over that travel         (firm)

# Strip geometry along its length.
L_SCALE_MM = 179.0     # infinity-to-MFD span                       (overlay: marks)
R_MM = L_SCALE_MM / (ROT_DEG * 3.141592653589793 / 180.0)  # wrap radius

# Strip outline.
STRIP_LEN_MM = 225.0   # tip to tip, includes the bent end tabs     (caliper)
STRIP_W_MM = 6.6       # strip width                                (caliper)
SLOT_SPAN_MM = 4.5     # mounting slot, curved end to curved end    (caliper)
SLOT_WIDTH_MM = 1.4    # slot width across the strip                (scan)
CORNER_R_MM = 1.0      # rounded outline corners                    (provisional)

# Placement within the strip frame (x measured from the left tab tip). The slot
# positions come from connected-component analysis of the stock scan; infinity
# is the infinity symbol's position relative to the left slot.
INF_OFFSET_MM = 27.8       # left tab tip to infinity, = slot + 23.1 (overlay)
LEFT_SLOT_X_MM = 4.7       # left slot center                        (scan)
CENTRAL_SLOT_X_MM = 118.6  # central slot center                     (scan)
RIGHT_SLOT_X_MM = 219.2    # right slot center                       (scan)

# Mark spacing along the strip.
MAX_MARK_GAP_MM = 15.0   # vision's 1.5cm ceiling                   (firm)
MIN_MARK_GAP_MM = 5.0    # anti-jumble floor                        (tunable)
SLOT_AVOID_MARGIN_MM = 1.0  # keep marks this far clear of a slot   (tunable)

# Focal lengths offered, in millimeters. The 40, 45, and 50 are the retrofocus
# wides flagged in the math doc; their HF stays 0 until a measurement says
# otherwise. 45, 85, and 105 have no manual data and are model extrapolations.
FOCAL_LENGTHS_MM = (40, 45, 50, 75, 80, 85, 100, 105, 135, 150, 200)

# Per-lens internodal offset, the hook for any future correction. Zero for all,
# which the stock strip confirms is good enough at present.
HF_MM = {f: 0.0 for f in FOCAL_LENGTHS_MM}

MAX_FOCAL_CHOICES = 3
