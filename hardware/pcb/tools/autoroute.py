"""First-pass autorouter for the picker box: a grid A* router on both copper layers, then GND pours on both sides.

    "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/pcb/tools/autoroute.py

Run with the board closed in KiCad (or reload it after). It REMOVES every existing track, via and zone first, so it is
only for starting the route; once tracks are hand-edited, edit them in KiCad instead of re-running this.

- 0.1 mm grid, octilinear moves (45/90 degree bends, no sharper), bend and via costs so the result stays tidy.
- Top layer preferred; the bottom costs more per mm so the bottom GND pour stays mostly whole.
- Every GND pad gets a short track to its own via (so it reaches the bottom pour); the pours connect the rest.
- Clearance 0.2 mm, copper to edge 0.5 mm, nothing within 3.2 mm of a mounting hole's centre (screw heads),
  vias kept off SMD pads and (by cost) off silkscreen.
"""
import heapq
import math
import os
import sys
import time
import numpy as np
import pcbnew
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(os.path.dirname(HERE), "picker-box.kicad_pcb")
OX = OY = 100.0
mm, tomm = pcbnew.FromMM, pcbnew.ToMM

G = 0.1                          # grid, mm
BW, BL, BR = 53.0, 82.0, 3.0     # board width, length, corner radius
NX, NY = int(round(BW / G)) + 1, int(round(BL / G)) + 1
NXY = NX * NY
CLR, SLOP, EDGE = 0.2, 0.05, 0.5
VIA_D, VIA_DRILL = 0.6, 0.3
HOLE_KEEPOUT = 3.2
POWER = {"/VCC", "/GND", "/VBAT"}
W_SIG, W_PWR = 0.25, 0.3
LAYER_COST = (1.0, 2.5)          # per mm, top / bottom
VIA_COST = 3.0                   # mm-equivalent
SILK_VIA_COST = 15.0
U1_RING_VIA_COST = 8.0
TURN_COST = (0.0, 0.8, 2.0)      # straight, 45 degrees, 90 degrees
MAX_EXPAND = 4_000_000

xs = np.arange(NX) * G
ys = np.arange(NY) * G
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


# ---------------------------------------------------------------- shapes and clearance maps
class Shape:
    def __init__(self, net, layers, kind, p):
        self.net, self.layers, self.kind, self.p = net, layers, kind, p
        if kind == "rect":
            self.bbox = p
        elif kind == "circle":
            cx, cy, r = p
            self.bbox = (cx - r, cy - r, cx + r, cy + r)
        else:  # seg
            x1, y1, x2, y2, hw = p
            self.bbox = (min(x1, x2) - hw, min(y1, y2) - hw, max(x1, x2) + hw, max(y1, y2) + hw)

    def dist(self, X, Y):
        if self.kind == "rect":
            x0, y0, x1, y1 = self.p
            dx = np.maximum(np.maximum(x0 - X, X - x1), 0)
            dy = np.maximum(np.maximum(y0 - Y, Y - y1), 0)
            return np.hypot(dx, dy)
        if self.kind == "circle":
            cx, cy, r = self.p
            return np.hypot(X - cx, Y - cy) - r
        x1, y1, x2, y2, hw = self.p
        vx, vy = x2 - x1, y2 - y1
        L2 = vx * vx + vy * vy
        t = np.clip(((X - x1) * vx + (Y - y1) * vy) / L2, 0, 1) if L2 > 0 else 0
        return np.hypot(X - (x1 + t * vx), Y - (y1 + t * vy)) - hw


# keys: track widths and the via; radius = how close a track centre / via centre may come to other copper
RADII = {W_SIG: CLR + W_SIG / 2 + SLOP, W_PWR: CLR + W_PWR / 2 + SLOP, "via": CLR + VIA_D / 2 + SLOP}
M = {k: np.zeros((2, NX, NY), np.int16) for k in RADII}


def stamp(maps, s, sign):
    for key, R in RADII.items():
        x0, y0, x1, y1 = s.bbox
        i0, i1 = max(0, int(math.floor((x0 - R) / G))), min(NX - 1, int(math.ceil((x1 + R) / G)))
        j0, j1 = max(0, int(math.floor((y0 - R) / G))), min(NY - 1, int(math.ceil((y1 + R) / G)))
        if i0 > i1 or j0 > j1:
            continue
        hit = (s.dist(xs[i0:i1 + 1, None], ys[None, j0:j1 + 1]) <= R).astype(np.int16) * sign
        for l in s.layers:
            maps[key][l, i0:i1 + 1, j0:j1 + 1] += hit


def edge_inside_distance():
    X, Y = xs[:, None], ys[None, :]
    qx = np.abs(X - BW / 2) - (BW / 2 - BR)
    qy = np.abs(Y - BL / 2) - (BL / 2 - BR)
    sd = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - BR
    return -sd


# ---------------------------------------------------------------- board
board = pcbnew.LoadBoard(PCB)
for t in list(board.GetTracks()):
    board.Remove(t)
for z in list(board.Zones()):
    board.Remove(z)

pads_by_net = {}
shapes = []
smd_pads = []
holes = []
for f in board.GetFootprints():
    for p in f.Pads():
        bb = p.GetBoundingBox()
        x0, y0 = tomm(bb.GetX()) - OX, tomm(bb.GetY()) - OY
        x1, y1 = x0 + tomm(bb.GetWidth()), y0 + tomm(bb.GetHeight())
        cx, cy = tomm(p.GetPosition().x) - OX, tomm(p.GetPosition().y) - OY
        attr = p.GetAttribute()
        if attr == pcbnew.PAD_ATTRIB_NPTH:
            holes.append((cx, cy))
            continue
        layers = (0,) if attr == pcbnew.PAD_ATTRIB_SMD else (0, 1)
        net = p.GetNetname()
        if p.GetShape(pcbnew.F_Cu) == pcbnew.PAD_SHAPE_CIRCLE:
            s = Shape(net, layers, "circle", (cx, cy, (x1 - x0) / 2))
        else:
            s = Shape(net, layers, "rect", (x0, y0, x1, y1))
        shapes.append(s)
        stamp(M, s, 1)
        if net == "/GND" and attr == pcbnew.PAD_ATTRIB_PTH:
            # keep other nets 0.6 mm further off through-hole GND pads, so the pours' thermal spokes all fit
            ring_s = Shape(net, layers, "circle", (cx, cy, (x1 - x0) / 2 + 0.6))
            shapes.append(ring_s)
            stamp(M, ring_s, 1)
        if attr == pcbnew.PAD_ATTRIB_SMD:
            smd_pads.append(s)
        if net:
            pads_by_net.setdefault(net, []).append(dict(ref=f.GetReference(), num=p.GetNumber(), x=cx, y=cy,
                                                        layers=layers, shape=s))

# static blocks: board edge and mounting-hole keep-outs (never own copper)
STATIC = {}
ed = edge_inside_distance()
for key, R in RADII.items():
    half = (key / 2) if key != "via" else VIA_D / 2
    blk = ed < EDGE + half + SLOP
    for hx, hy in holes:
        blk |= np.hypot(xs[:, None] - hx, ys[None, :] - hy) < HOLE_KEEPOUT + half
    STATIC[key] = blk
# vias never on an SMD pad (any net)
HOLE_R = VIA_DRILL / 2 + 0.25 + SLOP          # + the other hole's radius
hole_cnt = np.zeros((NX, NY), np.int16)


def stamp_hole(x, y, r, sign):
    i0, i1 = max(0, int((x - r) / G) - 1), min(NX - 1, int((x + r) / G) + 1)
    j0, j1 = max(0, int((y - r) / G) - 1), min(NY - 1, int((y + r) / G) + 1)
    hole_cnt[i0:i1 + 1, j0:j1 + 1] += (np.hypot(xs[i0:i1 + 1, None] - x, ys[None, j0:j1 + 1] - y) <= r) * sign


for f in board.GetFootprints():
    for q in f.Pads():
        if q.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            stamp_hole(tomm(q.GetPosition().x) - OX, tomm(q.GetPosition().y) - OY,
                       HOLE_R + tomm(q.GetDrillSize().x) / 2, 1)
no_via = np.zeros((NX, NY), bool)
for s in smd_pads:
    no_via |= s.dist(xs[:, None], ys[None, :]) <= VIA_D / 2 + 0.1

# via cost on silkscreen (logos, seat numbers, ISP labels), either side
silk = Image.new("L", (NY, NX), 0)   # PIL is (width=j, height=i)... drawn as (y, x) to match [i, j]
dr = ImageDraw.Draw(silk)
for d in board.GetDrawings():
    if d.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
        continue
    if d.GetClass() == "PCB_SHAPE" and d.GetShape() == pcbnew.SHAPE_T_POLY:
        ps = d.GetPolyShape()
        for o in range(ps.OutlineCount()):
            ol = ps.Outline(o)
            pts = [((tomm(ol.CPoint(n).y) - OY) / G, (tomm(ol.CPoint(n).x) - OX) / G) for n in range(ol.PointCount())]
            if len(pts) > 2:
                dr.polygon(pts, fill=255)
    elif d.GetClass() == "PCB_TEXT":
        bb = d.GetBoundingBox()
        x0, y0 = tomm(bb.GetX()) - OX, tomm(bb.GetY()) - OY
        dr.rectangle([y0 / G, x0 / G, (y0 + tomm(bb.GetHeight())) / G, (x0 + tomm(bb.GetWidth())) / G], fill=255)
silk = silk.filter(ImageFilter.MaxFilter(7))
silk_mask = np.array(silk).astype(bool)   # shape (NX, NY)
# vias also cost extra in the ring round U1 where its pins fan out (under the chip body is fine)
_u = next(f for f in board.GetFootprints() if f.GetReference() == "U1")
_ux, _uy = tomm(_u.GetPosition().x) - OX, tomm(_u.GetPosition().y) - OY
_X, _Y = np.abs(xs[:, None] - _ux), np.abs(ys[None, :] - _uy)
ring = (np.maximum(_X, _Y) < 7.0) & ~((_X < 3.0) & (_Y < 3.0))
VIA_PEN = (silk_mask * SILK_VIA_COST + ring * U1_RING_VIA_COST).ravel().tolist()

netinfo = {n: board.FindNet(n) for n in pads_by_net}
net_shapes = {}
for s in shapes:
    net_shapes.setdefault(s.net, []).append(s)


def own_maps(net):
    o = {k: np.zeros((2, NX, NY), np.int16) for k in RADII}
    for s in net_shapes.get(net, []):
        stamp(o, s, 1)
    return o


def blocked_bytes(own, w):
    bt = [((M[w][l] - own[w][l]) > 0) | STATIC[w] for l in (0, 1)]
    vfree = ~(((M["via"][0] - own["via"][0]) > 0) | ((M["via"][1] - own["via"][1]) > 0) | STATIC["via"] | no_via
              | (hole_cnt > 0))
    return bt[0].tobytes() + bt[1].tobytes(), vfree.tobytes()


# ---------------------------------------------------------------- A*
SQ2 = math.sqrt(2)


def astar(bt, vfree, sources, goals, hpt, lcost=(1.0, 2.5), to_bottom=False):
    """sources/goals: sets of (l, k) with k = i*NY + j. hpt: (i, j, layers) of the goal for the heuristic."""
    gi, gj, glayers = hpt

    def h(l, k):
        if to_bottom:
            return 0.0 if l == 1 else VIA_COST
        i, j = divmod(k, NY)
        dx, dy = abs(i - gi), abs(j - gj)
        v = (max(dx, dy) + (SQ2 - 1) * min(dx, dy)) * G * min(lcost)
        return v + (0 if l in glayers else VIA_COST)

    best = {}
    parent = {}
    heap = []
    for l, k in sources:
        s = (l * NXY + k) * 9 + 8
        best[s] = 0.0
        parent[s] = None
        heapq.heappush(heap, (h(l, k), 0.0, s))
    n = 0
    while heap:
        f, g, s = heapq.heappop(heap)
        if g > best.get(s, 1e18):
            continue
        d = s % 9
        lk = s // 9
        l, k = divmod(lk, NXY)
        if (to_bottom and l == 1) or (not to_bottom and (l, k) in goals):
            path = []
            while s is not None:
                lk = s // 9
                path.append(divmod(lk, NXY))
                s = parent[s]
            return path[::-1], g
        n += 1
        if n > MAX_EXPAND:
            return None, n
        i, j = divmod(k, NY)
        lc = lcost[l] * G
        base = l * NXY
        for nd, (di, dj) in enumerate(DIRS):
            if d != 8:
                m = abs(nd - d)
                m = min(m, 8 - m)
                if m > 2:
                    continue
                tc = TURN_COST[m]
            else:
                tc = 0.0
            ni, nj = i + di, j + dj
            if ni < 0 or nj < 0 or ni >= NX or nj >= NY:
                continue
            nk = ni * NY + nj
            if bt[base + nk]:
                continue
            ng = g + lc * (SQ2 if di and dj else 1.0) + tc
            ns = ((base + nk) * 9) + nd
            if ng < best.get(ns, 1e18):
                best[ns] = ng
                parent[ns] = s
                heapq.heappush(heap, (ng + h(l, nk), ng, ns))
        if vfree[k]:
            nl = 1 - l
            ng = g + VIA_COST + VIA_PEN[k]
            ns = ((nl * NXY + k) * 9) + 8
            if ng < best.get(ns, 1e18):
                best[ns] = ng
                parent[ns] = s
                heapq.heappush(heap, (ng + h(nl, k), ng, ns))
    return None, n


# ---------------------------------------------------------------- committing paths
added = {"tracks": 0, "vias": 0}
items = {}   # net -> [(board item, shape)] for tracks and vias (rip-up)


def P(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


def commit(net, w, path, own, tree):
    """Turn a cell path into tracks and vias on the board and into the clearance maps."""
    ni = netinfo[net]
    runs = []
    cur = [path[0]]
    for a, b in zip(path, path[1:]):
        if a[0] != b[0]:                       # via
            runs.append(cur)
            runs.append(("via", a[1]))
            cur = [b]
            continue
        if len(cur) >= 2:
            pa, pb = divmod(cur[-2][1], NY), divmod(cur[-1][1], NY)
            qa, qb = pb, divmod(b[1], NY)
            if (pb[0] - pa[0], pb[1] - pa[1]) != (qb[0] - qa[0], qb[1] - qa[1]):
                runs.append(cur)
                cur = [cur[-1]]
        cur.append(b)
    runs.append(cur)
    new = []
    for r in runs:
        if isinstance(r, tuple):
            i, j = divmod(r[1], NY)
            x, y = i * G, j * G
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(P(x, y))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetWidth(mm(VIA_D))
            v.SetDrill(mm(VIA_DRILL))
            v.SetNet(ni)
            board.Add(v)
            stamp_hole(x, y, HOLE_R + VIA_DRILL / 2, 1)
            added["vias"] += 1
            new.append((v, Shape(net, (0, 1), "circle", (x, y, VIA_D / 2))))
            continue
        if len(r) < 2:
            continue
        l = r[0][0]
        (i1, j1), (i2, j2) = divmod(r[0][1], NY), divmod(r[-1][1], NY)
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(P(i1 * G, j1 * G))
        t.SetEnd(P(i2 * G, j2 * G))
        t.SetWidth(mm(w))
        t.SetLayer(pcbnew.F_Cu if l == 0 else pcbnew.B_Cu)
        t.SetNet(ni)
        board.Add(t)
        added["tracks"] += 1
        new.append((t, Shape(net, (l,), "seg", (i1 * G, j1 * G, i2 * G, j2 * G, w / 2))))
    for obj, s in new:
        stamp(M, s, 1)
        stamp(own, s, 1)
        net_shapes.setdefault(net, []).append(s)
        items.setdefault(net, []).append((obj, s))
    tree.update(path)


def rip(net):
    for obj, s in items.pop(net, []):
        board.Remove(obj)
        if obj.GetClass() == "PCB_VIA":
            stamp_hole(s.p[0], s.p[1], HOLE_R + VIA_DRILL / 2, -1)
        stamp(M, s, -1)
        net_shapes[net].remove(s)
        added["vias" if obj.GetClass() == "PCB_VIA" else "tracks"] -= 1
    print(f"    ripped up {net}")


def nets_near(x, y, r, exclude):
    out = set()
    for n, lst in items.items():
        if n in exclude:
            continue
        for _, s in lst:
            if float(s.dist(np.array(x), np.array(y))) <= r:
                out.add(n)
                break
    return out


def cell(x, y):
    return int(round(x / G)), int(round(y / G))


def pad_goals(pad, bt):
    """The pad's centre cell(s) on its layers; if those are blocked, any free cell inside the pad."""
    i, j = cell(pad["x"], pad["y"])
    k = i * NY + j
    g = {(l, k) for l in pad["layers"] if not bt[l * NXY + k]}
    if g:
        return g
    x0, y0, x1, y1 = pad["shape"].bbox
    for ii in range(int(math.ceil(x0 / G)), int(math.floor(x1 / G)) + 1):
        for jj in range(int(math.ceil(y0 / G)), int(math.floor(y1 / G)) + 1):
            for l in pad["layers"]:
                kk = ii * NY + jj
                if not bt[l * NXY + kk]:
                    g.add((l, kk))
    return g


failed = []


LCOST = {"/MOSI": (1.6, 1.0), "/MISO": (1.6, 1.0), "/SCK": (1.6, 1.0), "/RESET": (1.6, 1.0),
         "/VCC": (1.0, 1.3), "/VBAT": (1.0, 1.3)}
first_pad = {}


def route_net(net, first=None, allow_rip=True):
    w = W_PWR if net in POWER else W_SIG
    lc = LCOST.get(net, (1.0, 2.5))
    first = first or first_pad.get(net)
    first_pad[net] = first
    own = own_maps(net)
    pads = list(pads_by_net[net])
    start = first if first is not None else pads[0]
    pads.remove(start)
    bt, vf = blocked_bytes(own, w)
    tree = set(pad_goals(start, bt))
    tree_xy = [(start["x"], start["y"])]
    while pads:
        # nearest remaining pad to anything already connected
        txy = np.array(tree_xy)
        pads.sort(key=lambda p: np.min(np.hypot(txy[:, 0] - p["x"], txy[:, 1] - p["y"])))
        p = pads.pop(0)
        bt, vf = blocked_bytes(own, w)
        goals = pad_goals(p, bt)
        if goals & tree:
            tree |= goals
            continue
        t0 = time.time()
        path, cost = astar(bt, vf, tree, goals, (*cell(p["x"], p["y"]), p["layers"]), lc)
        victims = set()
        if path is None and allow_rip:
            victims = nets_near(p["x"], p["y"], 3.0, {net, "/GND"}) | nets_near(start["x"], start["y"], 3.0, {net, "/GND"})
            print(f"  {net} -> {p['ref']}.{p['num']} blocked; ripping {sorted(victims)}")
            for v in victims:
                rip(v)
            bt, vf = blocked_bytes(own, w)
            goals = pad_goals(p, bt)
            path, cost = astar(bt, vf, tree, goals, (*cell(p["x"], p["y"]), p["layers"]), lc)
        if path is None:
            failed.append((net, p["ref"], p["num"]))
            print(f"  FAILED {net} -> {p['ref']}.{p['num']} ({cost} expansions)")
        else:
            commit(net, w, path, own, tree)
            tree |= goals
            tree_xy += [(divmod(k, NY)[0] * G, divmod(k, NY)[1] * G) for _, k in path[::5]] + [(p["x"], p["y"])]
            print(f"  {net} -> {p['ref']}.{p['num']}: {cost:.1f} ({time.time() - t0:.1f}s)")
        for v in sorted(victims):
            print(f"  re-routing {v}")
            route_net(v, allow_rip=False)


def gnd_escape(pad, allow_rip=True):
    """A short track from a GND pad to its own via."""
    net = "/GND"
    own = own_maps(net)
    bt, vf = blocked_bytes(own, W_PWR)
    src = pad_goals(pad, bt)
    path, cost = astar(bt, vf, src, None, (0, 0, (1,)), to_bottom=True)
    victims = set()
    if path is None and allow_rip:
        victims = nets_near(pad["x"], pad["y"], 2.5, {net})
        print(f"  GND via for {pad['ref']}.{pad['num']} blocked; ripping {sorted(victims)}")
        for v in victims:
            rip(v)
        bt, vf = blocked_bytes(own, W_PWR)
        src = pad_goals(pad, bt)
        path, cost = astar(bt, vf, src, None, (0, 0, (1,)), to_bottom=True)
    if path is None:
        failed.append((net, pad["ref"], pad["num"]))
        print(f"  FAILED GND via for {pad['ref']}.{pad['num']}")
    else:
        commit(net, W_PWR, path, own, set())
        print(f"  GND via for {pad['ref']}.{pad['num']}: {cost:.1f}")
    for v in sorted(victims):
        print(f"  re-routing {v}")
        route_net(v, allow_rip=False)


def pad(ref, num):
    for ps in pads_by_net.values():
        for p in ps:
            if p["ref"] == ref and p["num"] == num:
                return p


# ---------------------------------------------------------------- order
t_all = time.time()
gnd_smd = [p for p in pads_by_net["/GND"] if p["layers"] == (0,)]
first_gnd = [p for p in gnd_smd if p["ref"] in ("U1", "CAVCC", "CAREF", "CDEC1", "CDEC2", "CBULK", "QBAT")]
print("U1 and capacitor GND pins")
for p in first_gnd:
    gnd_escape(p)

nets = [n for n in pads_by_net if n not in ("/GND", "/VCC") and len(pads_by_net[n]) > 1]


def span(n):
    ps = pads_by_net[n]
    return max(math.hypot(a["x"] - b["x"], a["y"] - b["y"]) for a in ps for b in ps)


k_nets = sorted([n for n in nets if n.endswith("_K")], key=span)
isp_nets = ["/RESET", "/SCK", "/MISO", "/MOSI"]
mcu_nets = sorted([n for n in nets if n not in k_nets and n not in isp_nets and n != "/VBAT"], key=span)
print("LED cathode nets")
for n in k_nets:
    route_net(n)
print("programming nets (bottom preferred)")
for n in isp_nets:
    route_net(n, first=next((p for p in pads_by_net[n] if p["ref"] == "U1"), None))
print("MCU nets, nearest first")
for n in mcu_nets:
    route_net(n, first=next((p for p in pads_by_net[n] if p["ref"] == "U1"), None))
print("VBAT")
route_net("/VBAT", first=pad("QBAT", "3"))
print("VCC")
route_net("/VCC", first=pad("QBAT", "2"))
print("GND vias")
for p in gnd_smd:
    if p not in first_gnd:
        gnd_escape(p)

# second chance for anything that failed: route it again with rip-up allowed
for rnd in range(2):
    if not failed:
        break
    todo, failed[:] = list(dict.fromkeys(failed)), []
    print(f"retry round {rnd + 1}: {todo}")
    for net, ref, num in todo:
        if net == "/GND":
            gnd_escape(pad(ref, num))
        elif (net, ref, num) not in [(a, b, c) for a, b, c in failed]:
            rip(net)
            route_net(net)

# ---------------------------------------------------------------- GND pours, both sides
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(netinfo["/GND"])
    z.SetZoneName("GND")
    o = z.Outline()
    o.NewOutline()
    for x, y in ((0, 0), (BW, 0), (BW, BL), (0, BL)):
        o.Append(mm(OX + x), mm(OY + y))
    z.SetLocalClearance(mm(0.25))
    z.SetMinThickness(mm(0.25))
    z.SetThermalReliefGap(mm(0.3))
    z.SetThermalReliefSpokeWidth(mm(0.4))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    board.Add(z)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())


# ---------------------------------------------------------------- stitch every pour fragment into one GND
def gnd_connectivity():
    """Union-find over the filled fragments of both layers, joined by GND vias and through-hole GND pads."""
    frags = []
    for z in board.Zones():
        for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
            if not z.IsOnLayer(lay):
                continue
            fp = z.GetFilledPolysList(lay)
            for i in range(fp.OutlineCount()):
                one = pcbnew.SHAPE_POLY_SET()
                one.AddOutline(fp.Outline(i))
                for j in range(fp.HoleCount(i)):
                    one.AddHole(fp.Hole(i, j))
                frags.append((lay, one, abs(fp.Outline(i).Area())))
    parent = list(range(len(frags)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    joins = [v.GetPosition() for v in board.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == "/GND"]
    joins += [q.GetPosition() for f in board.GetFootprints() for q in f.Pads()
              if q.GetNetname() == "/GND" and q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    for pos in joins:
        inside = [n for n, (lay, poly, _) in enumerate(frags) if poly.Contains(pos)]
        for n in inside[1:]:
            parent[find(n)] = find(inside[0])
    comps = {}
    for n in range(len(frags)):
        comps.setdefault(find(n), []).append(n)
    return frags, comps


def add_via(x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(P(x, y))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetWidth(mm(VIA_D))
    v.SetDrill(mm(VIA_DRILL))
    v.SetNet(netinfo["/GND"])
    board.Add(v)
    added["vias"] += 1
    s = Shape("/GND", (0, 1), "circle", (x, y, VIA_D / 2))
    stamp(M, s, 1)
    net_shapes["/GND"].append(s)
    stamp_hole(x, y, HOLE_R + VIA_DRILL / 2, 1)


def stitch_ok():
    _, vf = blocked_bytes(own_maps("/GND"), W_PWR)
    return np.frombuffer(vf, bool).reshape(NX, NY) & ~silk_mask & ~ring


def well_inside(poly, x, y):
    """The via's whole pad is inside the fragment (centre and 8 points round it, with zone clearance)."""
    r = VIA_D / 2 + 0.1
    pts = [(x, y)] + [(x + r * math.cos(a * math.pi / 4), y + r * math.sin(a * math.pi / 4)) for a in range(8)]
    return all(poly.Contains(P(px, py)) for px, py in pts)


# 1. islands: give each fragment group that is not part of the main GND a via into the main group
for it in range(12):
    frags, comps = gnd_connectivity()
    area = {c: sum(frags[n][2] for n in ns) for c, ns in comps.items()}
    main = max(area, key=area.get)
    others = [c for c in comps if c != main]
    if not others:
        print(f"GND pours: one connected whole ({len(frags)} fragments)")
        break
    ok = stitch_ok()
    fixed = 0
    for c in others:
        done = False
        for n in comps[c]:
            lay, poly, _ = frags[n]
            bb = poly.BBox()
            for i in range(max(0, int((tomm(bb.GetX()) - OX) / G)), min(NX, int((tomm(bb.GetRight()) - OX) / G) + 1), 2):
                for j in range(max(0, int((tomm(bb.GetY()) - OY) / G)), min(NY, int((tomm(bb.GetBottom()) - OY) / G) + 1), 2):
                    if not ok[i, j]:
                        continue
                    x, y = i * G, j * G
                    if not well_inside(poly, x, y):
                        continue
                    if any(frags[m][0] != lay and well_inside(frags[m][1], x, y) for m in range(len(frags))
                           if m not in comps[c]):
                        add_via(x, y)
                        ok = stitch_ok()
                        done = True
                        break
                if done:
                    break
            if done:
                break
        fixed += done
    print(f"GND pours: {len(others)} separate groups, stitched {fixed}")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    if not fixed:
        # no room for a via: join each separate group to the rest with a GND track instead
        for c in others:
            in_c = lambda pos: any(frags[n][1].Contains(pos) for n in comps[c])
            src, goals = set(), set()
            for v in board.GetTracks():
                if v.GetClass() == "PCB_VIA" and v.GetNetname() == "/GND":
                    i, j = cell(tomm(v.GetPosition().x) - OX, tomm(v.GetPosition().y) - OY)
                    (src if in_c(v.GetPosition()) else goals).update({(0, i * NY + j), (1, i * NY + j)})
            for q in pads_by_net["/GND"]:
                i, j = cell(q["x"], q["y"])
                (src if in_c(P(q["x"], q["y"])) else goals).update({(l, i * NY + j) for l in q["layers"]})
            own = own_maps("/GND")
            bt, vf = blocked_bytes(own, W_PWR)
            ci, cj = np.mean([divmod(k, NY) for _, k in src], axis=0)
            gk = min(goals, key=lambda g: math.hypot(divmod(g[1], NY)[0] - ci, divmod(g[1], NY)[1] - cj))
            path, cost = astar(bt, vf, src, goals, (*divmod(gk[1], NY), (0, 1)))
            if path is None:
                print("  could not join a GND group:", [(board.GetLayerName(frags[n][0]), round(frags[n][2] / 1e12, 1)) for n in comps[c]])
            else:
                commit("/GND", W_PWR, path, own, set())
                print(f"  joined a GND group with a track ({cost:.1f})")
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())

# 2. a light grid of stitching vias where both pours are solid, away from silk and the U1 fan-out
ok = stitch_ok()
frags, comps = gnd_connectivity()
n_st = 0
for gx in [float(v) for v in np.arange(3.0, BW - 2.9, 5.0)]:
    for gy in [float(v) for v in np.arange(3.0, BL - 2.9, 5.0)]:
        i, j = int(round(gx / G)), int(round(gy / G))
        if ok[i, j] and all(any(frags[m][0] == lay and well_inside(frags[m][1], gx, gy) for m in range(len(frags)))
                            for lay in (pcbnew.F_Cu, pcbnew.B_Cu)):
            add_via(gx, gy)
            ok = stitch_ok()
            n_st += 1
print(f"grid stitching vias: {n_st}")
pcbnew.ZONE_FILLER(board).Fill(board.Zones())

board.Save(PCB)
print(f"done in {time.time() - t_all:.0f}s: {added['tracks']} tracks, {added['vias']} vias; failed: {failed}")
