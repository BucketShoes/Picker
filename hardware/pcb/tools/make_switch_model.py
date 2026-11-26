"""HAND-MADE 3D model of the BZCN TSF002A05526A 12x12 tactile switch (C2888711). Not from a reference source.

    py hardware/pcb/tools/make_switch_model.py

Writes hardware/pcb/lib/handmade.3dshapes/HANDMADE_TSF002A05526A.wrl. EasyEDA's model for this part is a different
switch (7.35 mm tall, square red stem), so this one was drawn from the BZCN TSF002******* drawing (2021.06.01):
  body 12 x 12, body height 3.2 (top of the cover), total height H = 5.5 (code 055), plunger dia 6.8,
  legs 1.0 wide x 0.3 thick at y +-2.5 (pitch 5), 15.0 tip to tip; body and plunger black PPA,
  cover tin-plated steel, legs silver-plated brass.
Not on the drawing, so guessed: cover plate thickness 0.2, cover opening dia 7.2, the four corner posts
(dia 1.2 at +-4.6), the 0.3 mm top chamfer on the plunger, the body's 0.15 mm stand-off and the leg bend shape.
Origin is the switch centre on the board surface; units are KiCad VRML units (0.1 inch).
"""
import math
import os

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "handmade.3dshapes",
                   "HANDMADE_TSF002A05526A.wrl")
U = 1 / 2.54  # mm -> 0.1 inch
N = 64        # segments per circle

BLACK = (0.08, 0.08, 0.09)
TIN = (0.72, 0.72, 0.74)
SILVER = (0.85, 0.85, 0.87)


class Mesh:
    def __init__(self):
        self.pts, self.faces = [], []

    def p(self, x, y, z):
        self.pts.append((x, y, z))
        return len(self.pts) - 1

    def face(self, *idx):
        self.faces.append(idx)


def prism(m, poly, z0, z1):
    """Extrude a convex polygon (counter-clockwise, seen from above) from z0 to z1."""
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


def circle(cx, cy, r, n=N):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def lathe(m, profile, n=N):
    """Revolve a profile [(r, z), ...] about the z axis; r == 0 points close the ends."""
    rings = []
    for r, z in profile:
        rings.append([m.p(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), z) for i in range(n)])
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            m.face(a[i], b[i], b[j], a[j])


def square_with_hole(m, half, r, z0, z1, n=N):
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
    lathe(m, [(r, z0), (r, z1)], n)              # hole wall
    for (x0, y0, x1, y1) in ((-half, -half, half, -half), (half, -half, half, half),
                             (half, half, -half, half), (-half, half, -half, -half)):
        a, b = m.p(x0, y0, z0), m.p(x1, y1, z0)
        c, d = m.p(x1, y1, z1), m.p(x0, y0, z1)
        m.face(a, b, c, d)


def shape(m, color, shiny=0.3):
    pts = ",\n".join("%.4f %.4f %.4f" % (x * U, y * U, z * U) for x, y, z in m.pts)
    idx = ",\n".join(", ".join(str(i) for i in f) + ", -1" for f in m.faces)
    return ("Shape {\n appearance Appearance { material Material { diffuseColor %.3f %.3f %.3f "
            "specularColor 0.3 0.3 0.3 shininess %.2f } }\n"
            " geometry IndexedFaceSet { ccw TRUE solid FALSE\n  coord Coordinate { point [\n%s\n ] }\n"
            "  coordIndex [\n%s\n ] }\n}\n") % (color + (shiny, pts, idx))


body, cover, plunger, legs = Mesh(), Mesh(), Mesh(), Mesh()

box(body, -6.0, 6.0, -6.0, 6.0, 0.15, 2.95)                 # housing
for sx in (-1, 1):
    for sy in (-1, 1):
        prism(body, circle(sx * 4.6, sy * 4.6, 0.6, 24), 2.95, 3.2)   # corner posts through the cover

square_with_hole(cover, 5.7, 3.6, 2.95, 3.15)                # metal cover plate

lathe(plunger, [(0.0, 5.5), (3.1, 5.5), (3.4, 5.2), (3.4, 3.15), (3.4, 2.95), (0.0, 2.95)])   # dia 6.8 to H 5.5

for sx in (-1, 1):                                           # gull-wing legs, 15.0 tip to tip
    for y in (-2.5, 2.5):
        y0, y1 = y - 0.5, y + 0.5
        lo, hi = sorted((sx * 6.0, sx * 6.6))
        box(legs, lo, hi, y0, y1, 0.7, 1.0)                  # out of the housing
        lo, hi = sorted((sx * 6.3, sx * 6.6))
        box(legs, lo, hi, y0, y1, 0.0, 1.0)                  # down
        lo, hi = sorted((sx * 6.3, sx * 7.5))
        box(legs, lo, hi, y0, y1, 0.0, 0.3)                  # foot on the pad

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("#VRML V2.0 utf8\n# HAND-MADE model of BZCN TSF002A05526A (C2888711), from the BZCN drawing. "
            "See hardware/pcb/tools/make_switch_model.py for what is measured and what is guessed.\n")
    for m, c, s in ((body, BLACK, 0.2), (cover, TIN, 0.6), (plunger, BLACK, 0.3), (legs, SILVER, 0.6)):
        f.write(shape(m, c, s))
print("wrote", OUT)
