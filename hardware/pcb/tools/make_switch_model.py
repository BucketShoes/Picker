"""HAND-MADE 3D models of BZCN TSF002A 12x12 tactile switches. Not from a reference source.

    py hardware/pcb/tools/make_switch_model.py            (all heights below)
    py hardware/pcb/tools/make_switch_model.py 4.5        (one height, mm)

Writes hardware/pcb/lib/handmade.3dshapes/HANDMADE_TSF002A0<HH>26A.wrl (e.g. ...04526A for H = 4.5).
EasyEDA's model for C2888711 (H 5.5) is a different switch (7.35 mm tall, square red stem), so these are drawn from the
BZCN TSF002******* drawing (2021.06.01). Only the plunger length differs between heights (the H code), as on the drawing.

Measured from the drawing (dimensioned, or scaled off it at about 22 px/mm against the 12 mm body):
  body 12 x 12, 3.2 tall to the top of the rim (dimensioned), 0.3 stand-off under the body (dimensioned 0.3),
  legs 1.0 wide x 0.3 thick at y +-2.5, 15.0 tip to tip (dimensioned), plunger dia 6.8 (dimensioned),
  rim about 0.95 wide (scaled), metal plate inset inside it with a dia 7.2 opening (scaled),
  four domes about dia 1.75 at +-4.05 from centre, tops about 0.55 above the rim (scaled),
  plunger top face about dia 6.3 with a rounded edge (scaled).
Guessed: how far the plate sits below the rim (0.22), the dome and edge profiles, the leg bend shape.
Colours from the drawing's parts table: body and plunger black PPA, plate tin-plated steel, legs silver-plated brass.
Origin is the switch centre on the board surface; units are KiCad VRML units (0.1 inch).
"""
import math
import os
import sys

DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "handmade.3dshapes")
U = 1 / 2.54  # mm -> 0.1 inch
N = 64        # segments per circle

BLACK = (0.07, 0.07, 0.08)
TIN = (0.70, 0.71, 0.73)
SILVER = (0.85, 0.85, 0.87)

RIM_TOP = 3.2      # body height (dimensioned)
STANDOFF = 0.3     # body bottom above the board (dimensioned)
RIM_W = 0.95       # rim width
PLATE_TOP = 2.98   # guessed: 0.22 below the rim
HOLE_R = 3.6       # plate opening
DOME_XY, DOME_R, DOME_TOP = 4.05, 0.875, 3.75
PLUNGER_R, PLUNGER_TOP_R = 3.4, 3.15


class Mesh:
    def __init__(self):
        self.pts, self.faces = [], []

    def p(self, x, y, z):
        self.pts.append((x, y, z))
        return len(self.pts) - 1

    def face(self, *idx):
        self.faces.append(idx)


def prism(m, poly, z0, z1):
    """Extrude a convex polygon (counter-clockwise from above) from z0 to z1. Faces wound outwards."""
    b = [m.p(x, y, z0) for x, y in poly]
    t = [m.p(x, y, z1) for x, y in poly]
    m.face(*t)
    m.face(*reversed(b))
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        m.face(b[i], b[j], t[j], t[i])


def box(m, x0, x1, y0, y1, z0, z1):
    prism(m, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1)


def lathe(m, profile, cx=0.0, cy=0.0, n=N):
    """Revolve [(r, z), ...] about a vertical axis at (cx, cy). Order the profile from the top centre outwards and down,
    so the faces point outwards; r == 0 points close the ends."""
    rings = [[m.p(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), z) for i in range(n)]
             for r, z in profile]
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            m.face(a[i], b[i], b[j], a[j])


def plate_with_hole(m, half, r, z0, z1, n=N):
    """Square plate (side 2*half) with a central round hole of radius r."""
    def sq(a):
        c, s = math.cos(a), math.sin(a)
        k = half / max(abs(c), abs(s))
        return c * k, s * k
    angles = [2 * math.pi * i / n for i in range(n)]
    for z, up in ((z1, True), (z0, False)):
        inner = [m.p(r * math.cos(a), r * math.sin(a), z) for a in angles]
        outer = [m.p(*sq(a), z) for a in angles]
        for i in range(n):
            j = (i + 1) % n
            q = (inner[i], inner[j], outer[j], outer[i])
            m.face(*(reversed(q) if up else q))
    lathe(m, [(r, z0), (r, z1)], n=n)          # hole wall, facing the axis
    for (x0, y0, x1, y1) in ((-half, -half, half, -half), (half, -half, half, half),
                             (half, half, -half, half), (-half, half, -half, -half)):
        a, b = m.p(x0, y0, z0), m.p(x1, y1, z0)
        c, d = m.p(x1, y1, z1), m.p(x0, y0, z1)
        m.face(a, b, c, d)


def shape(m, color, shiny):
    pts = ",\n".join("%.4f %.4f %.4f" % (x * U, y * U, z * U) for x, y, z in m.pts)
    idx = ",\n".join(", ".join(str(i) for i in f) + ", -1" for f in m.faces)
    return ("Shape {\n appearance Appearance { material Material { diffuseColor %.3f %.3f %.3f "
            "specularColor 0.3 0.3 0.3 shininess %.2f } }\n"
            " geometry IndexedFaceSet { ccw TRUE solid FALSE\n  coord Coordinate { point [\n%s\n ] }\n"
            "  coordIndex [\n%s\n ] }\n}\n") % (color + (shiny, pts, idx))


def build(h):
    body, plate, plunger, legs = Mesh(), Mesh(), Mesh(), Mesh()
    inner = 6.0 - RIM_W
    box(body, -6.0, 6.0, -6.0, 6.0, STANDOFF, PLATE_TOP - 0.1)                  # housing below the plate
    for x0, x1, y0, y1 in ((-6.0, 6.0, -6.0, -inner), (-6.0, 6.0, inner, 6.0),    # raised rim round the edge
                           (-6.0, -inner, -inner, inner), (inner, 6.0, -inner, inner)):
        box(body, x0, x1, y0, y1, PLATE_TOP - 0.1, RIM_TOP)
    for sx in (-1, 1):                                                           # corner domes on the plate
        for sy in (-1, 1):
            prof = [(0.0, DOME_TOP)]
            hgt = DOME_TOP - PLATE_TOP
            for k in range(1, 7):
                a = k / 6 * math.pi / 2
                prof.append((DOME_R * math.sin(a), PLATE_TOP + hgt * math.cos(a)))
            prof.append((0.0, PLATE_TOP))
            lathe(body, prof, sx * DOME_XY, sy * DOME_XY, 32)
    plate_with_hole(plate, inner, HOLE_R, PLATE_TOP - 0.1, PLATE_TOP)
    e = PLUNGER_R - PLUNGER_TOP_R                                                # rounded top edge
    prof = [(0.0, h), (PLUNGER_TOP_R, h)]
    for k in range(1, 5):
        a = k / 4 * math.pi / 2
        prof.append((PLUNGER_TOP_R + e * math.sin(a), h - e * (1 - math.cos(a))))
    prof += [(PLUNGER_R, PLATE_TOP - 0.1), (0.0, PLATE_TOP - 0.1)]
    lathe(plunger, prof)
    for sx in (-1, 1):                                                           # gull-wing legs
        for y in (-2.5, 2.5):
            y0, y1 = y - 0.5, y + 0.5
            for a, b, z0, z1 in ((6.0, 6.5, 0.3, 0.6), (6.2, 6.5, 0.0, 0.6), (6.2, 7.5, 0.0, 0.3)):
                lo, hi = sorted((sx * a, sx * b))
                box(legs, lo, hi, y0, y1, z0, z1)
    name = "HANDMADE_TSF002A0%02d26A.wrl" % round(h * 10)
    os.makedirs(DIR, exist_ok=True)
    with open(os.path.join(DIR, name), "w", encoding="utf-8", newline="\n") as f:
        f.write("#VRML V2.0 utf8\n# HAND-MADE model of BZCN TSF002A0%02d26A (H %.1f mm), from the BZCN drawing. "
                "See hardware/pcb/tools/make_switch_model.py for what is measured and what is guessed.\n" % (round(h * 10), h))
        for m, c, s in ((body, BLACK, 0.2), (plate, TIN, 0.6), (plunger, BLACK, 0.3), (legs, SILVER, 0.6)):
            f.write(shape(m, c, s))
    print("wrote", name)


for h in ([float(a) for a in sys.argv[1:]] or [4.3, 4.5, 5.0, 5.5]):
    build(h)
