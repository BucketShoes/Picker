"""Put the club logo (hardware/art/exiles-logo.png) on an existing board as filled silkscreen, replacing any logo
already in the given area. Run with KiCad 10's Python, with KiCad closed (or reload the board after):

    "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/pcb/tools/silk_logo.py <F|B> <cx> <cy> <height> [--text]

Positions are mm from the board's top-left corner (KiCad 100,100). The white skull becomes silk; with --text the grey
club name is cut out of it (only legible at large sizes). B (back) is mirrored so it reads correctly from behind.
"""
import os
import sys
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(os.path.dirname(HERE), "picker-box.kicad_pcb")
PNG = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art", "exiles-logo.png")
OX = OY = 100.0
mm = pcbnew.FromMM


def logo_polys(board, layer, cx, cy, height, with_text, mirror):
    from PIL import Image
    im = Image.open(PNG).convert("RGB")
    lo = 195 if with_text else 140      # the club name is grey (~165) on the white (~245) skull

    def silk(rgb):
        return min(rgb) > lo and max(rgb) - min(rgb) < 30
    px = im.load()
    w, h = im.size
    cols = [x for x in range(w) if any(silk(px[x, y]) for y in range(h))]
    rows = [y for y in range(h) if any(silk(px[x, y]) for x in range(w))]
    x0, x1, y0, y1 = cols[0], cols[-1] + 1, rows[0], rows[-1] + 1
    k = height / (y1 - y0)
    sps = pcbnew.SHAPE_POLY_SET()

    def add_rect(ax, bx, ay, by):
        X = [cx + ((x0 + x1) / 2 - v) * k if mirror else cx + (v - (x0 + x1) / 2) * k for v in (ax, bx)]
        Y = [cy + (v - (y0 + y1) / 2) * k for v in (ay, by)]
        o = sps.NewOutline()
        for xx, yy in ((X[0], Y[0]), (X[1], Y[0]), (X[1], Y[1]), (X[0], Y[1])):
            sps.Append(mm(OX + xx), mm(OY + yy), o)
    for y in range(y0, y1):
        x = x0
        while x < x1:
            if silk(px[x, y]):
                s0 = x
                while x < x1 and silk(px[x, y]):
                    x += 1
                add_rect(s0, x, y, y + 1)
            x += 1
    sps.Simplify()
    out = []
    for i in range(sps.OutlineCount()):
        one = pcbnew.SHAPE_POLY_SET()
        one.AddOutline(sps.Outline(i))
        for j in range(sps.HoleCount(i)):
            one.AddHole(sps.Hole(i, j))
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_POLY)
        s.SetLayer(layer); s.SetPolyShape(one); s.SetFilled(True); s.SetWidth(0)
        out.append(s)
    return out, k * (x1 - x0)


def place_logo(board, side, cx, cy, height, with_text):
    layer = pcbnew.F_SilkS if side == "F" else pcbnew.B_SilkS
    polys, width = logo_polys(board, layer, cx, cy, height, with_text, side == "B")
    # remove filled silk polygons in the area the new logo covers (the old logo), generously
    area = pcbnew.BOX2I(pcbnew.VECTOR2I(mm(OX + cx - width), mm(OY + cy - height)),
                        pcbnew.VECTOR2I(mm(2 * width), mm(2 * height)))
    old = [d for d in board.GetDrawings() if d.GetClass() == "PCB_SHAPE" and d.GetLayer() == layer
           and d.GetShape() == pcbnew.SHAPE_T_POLY and area.Contains(d.GetBoundingBox())]
    for d in old:
        board.Remove(d)
    for s in polys:
        board.Add(s)
    print(f"logo {side}: removed {len(old)} old polygons, added {len(polys)}; {width:.1f} x {height:.1f} mm at ({cx}, {cy})")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    b = pcbnew.LoadBoard(PCB)
    place_logo(b, a[0], float(a[1]), float(a[2]), float(a[3]), "--text" in sys.argv)
    b.Save(PCB)
