"""Build the picker-box board: outline, placed footprints and nets. No tracks.

Run with KiCad 10's Python:
    "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/pcb/tools/build_board.py

This is a starting point for the KiCad files, not their source: once the board has been edited in KiCad,
edit the board, not this script.
"""
import os
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB_DIR = os.path.dirname(HERE)
LIB = os.path.join(PCB_DIR, "lib", "PickerBox.pretty")
KICAD_FP = r"C:/Program Files/KiCad/10.0/share/kicad/footprints"
OUT = os.path.join(PCB_DIR, "picker-box.kicad_pcb")

W, L, R_CORNER = 53.0, 82.0, 3.0      # board, mm
OX, OY = 100.0, 100.0                 # board top-left in KiCad coordinates
CX = W / 2                            # middle of the board
COL = 17.6                            # switch column offset from the middle
ROWS = [6.5, 29.5, 52.5, 75.5]        # switch row centres (corners at top and bottom)

board = pcbnew.BOARD()
mm = pcbnew.FromMM


def pt(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


nets = {}


def net(name):
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        nets[name] = n
    return nets[name]


def place(lib, fp_name, ref, value, x, y, rot=0, lcsc=None, pads=None, dnp=False):
    fp = pcbnew.FootprintLoad(lib, fp_name)
    if fp is None:
        raise SystemExit(f"footprint not found: {lib} {fp_name}")
    fp.SetReference(ref)
    fp.SetValue(value)
    board.Add(fp)
    fp.SetPosition(pt(x, y))
    fp.SetOrientationDegrees(rot)
    if lcsc:
        f = pcbnew.PCB_FIELD(fp, pcbnew.FIELD_T_USER, "LCSC Part #")
        f.SetText(lcsc)
        f.SetVisible(False)
        fp.Add(f)
    if dnp:
        fp.SetDNP(True)
        fp.SetExcludedFromBOM(True)
        fp.SetExcludedFromPosFiles(True)
    for pad_num, net_name in (pads or {}).items():
        hits = [p for p in fp.Pads() if p.GetNumber() == str(pad_num)]
        if not hits:
            raise SystemExit(f"{ref}: no pad {pad_num}")
        for p in hits:
            p.SetNet(net(net_name))
    return fp


# ---- outline: rounded rectangle on Edge.Cuts
def edge_line(x1, y1, x2, y2):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(pt(x1, y1)); s.SetEnd(pt(x2, y2)); s.SetWidth(mm(0.1))
    board.Add(s)


def edge_arc(cx, cy, sx, sy, angle):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetCenter(pt(cx, cy)); s.SetStart(pt(sx, sy)); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
    s.SetWidth(mm(0.1))
    board.Add(s)


r = R_CORNER
edge_line(r, 0, W - r, 0); edge_line(W, r, W, L - r); edge_line(W - r, L, r, L); edge_line(0, L - r, 0, r)
edge_arc(W - r, r, W - r, 0, 90); edge_arc(W - r, L - r, W, L - r, 90)
edge_arc(r, L - r, r, L, 90); edge_arc(r, r, 0, r, 90)

# ---- MCU and its pin map (ATmega328P-AU, TQFP-32). Guidance only: fixed at the netlist stage.
U1_PINS = {
    3: "GND", 5: "GND", 21: "GND", 4: "VCC", 6: "VCC", 18: "VCC", 20: "AREF",
    29: "RESET", 15: "MOSI", 16: "MISO", 17: "SCK", 26: "MODE",
}
# seat: (LED pin number, LED port, button pin number, button port)
SEATS = {
    1: (10, "PD6", 11, "PD7"),
    2: (9, "PD5", 2, "PD4"),
    3: (13, "PB1", 12, "PB0"),
    4: (14, "PB2", 7, "PB6"),
    5: (1, "PD3", 8, "PB7"),
    6: (30, "PD0", 23, "PC0"),
    7: (31, "PD1", 24, "PC1"),
    8: (32, "PD2", 25, "PC2"),
}
for s, (lp, lport, bp, bport) in SEATS.items():
    U1_PINS[lp] = f"LED{s}"
    U1_PINS[bp] = f"BTN{s}"

place(LIB, "TQFP-32_L7.0-W7.0-P0.80-LS9.0-BL", "U1", "ATmega328P-AU", CX, 16.0, 0, "C14877", U1_PINS)

# ---- seats: left column top to bottom = 1..4, right column bottom to top = 5..8
# Switch: BZCN TSF002A05526A (C2888711). Its EasyEDA land is 18 mm across the pads (pads 3.0 x 1.7 at x +-7.5, y +-2.5).
# Corner switches sit 3 mm in from the middle-row columns, unrotated: pads left/right, LEDs just past the pad ends.
# Middle switches are turned 90 deg (pads top/bottom) so their 18 mm land clears the cell holder; LEDs beside the plain sides.
CORNER_COL = COL - 3.0
seats = {  # seat: (x offset from middle, row y, rotation, LED offset from switch centre, resistor y offset, resistor rotation)
    1: (-CORNER_COL, ROWS[0], 0, 10.0, 8.0, 90),
    2: (-COL, ROWS[1], 90, 6.8, 10.1, 0),
    3: (-COL, ROWS[2], 90, 6.8, -10.1, 0),
    4: (-CORNER_COL, ROWS[3], 0, 10.0, -8.0, 90),
    5: (CORNER_COL, ROWS[3], 0, 10.0, -8.0, 90),
    6: (COL, ROWS[2], 90, 6.8, -10.1, 0),
    7: (COL, ROWS[1], 90, 6.8, 10.1, 0),
    8: (CORNER_COL, ROWS[0], 0, 10.0, 8.0, 90),
}

for s, (dx, y, rot, led_off, res_dy, res_rot) in seats.items():
    x = CX + dx
    place(LIB, "KEY-SMD_4P-L12.0-W12.0-P5.00-LS15.0", f"SW{s}", "TSF002A05526A", x, y, rot, "C2888711",
          {1: f"BTN{s}", 2: f"BTN{s}", 3: "GND", 4: "GND"})
    outer = -1 if dx < 0 else 1
    # LED A outside (towards the player), LED B inside (towards the middle). On the middle (turned) switches the inner LED
    # is for players across the board, so it moves 4.5 mm towards the nearer short edge, out past the end of the cell
    # holder, while staying alongside its own switch (within the 12 mm body length).
    for tag, side in (("A", outer), ("B", -outer)):
        ly = y
        if rot == 90 and tag == "B":
            ly = y + (-4.5 if y < L / 2 else 4.5)
        place(LIB, "LED-SMD_L1.6-W0.8-R-RD", f"LED{s}{tag}", "KT-0603R red", x + side * led_off, ly, 90, "C2286",
              {1: "VCC", 2: f"LED{s}{tag}_K"})
    ry = y + res_dy
    for tag, rx in (("A", x + outer * 3.0), ("B", x - outer * 3.0)):
        place(LIB, "R0603", f"RL{s}{tag}", "270", rx, ry, res_rot, "C22966", {1: f"LED{s}", 2: f"LED{s}{tag}_K"})
    t = pcbnew.PCB_TEXT(board)
    t.SetText(str(s)); t.SetLayer(pcbnew.F_SilkS); t.SetPosition(pt(x, ry))
    size = 2.0 if rot == 0 else 1.5
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(0.25))
    board.Add(t)

# ---- power
place(LIB, "BAT-SMD_XDCR-2032-603", "BAT1", "XDCR-2032-603", CX, 41.0, 90, "C7498148", {1: "VBAT", 2: "GND"})
# reference outline of the 20 mm cell, centred in the holder
cell = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_CIRCLE)
cell.SetLayer(pcbnew.F_SilkS); cell.SetCenter(pt(CX, 41.0)); cell.SetEnd(pt(CX + 10.0, 41.0)); cell.SetWidth(mm(0.15))
board.Add(cell)
place(LIB, "SOT-23_L2.9-W1.3-P1.90-LS2.4-BR", "QBAT", "AO3401A", CX + 8.5, 14.5, 0, "C15127",
      {1: "GND", 2: "VCC", 3: "VBAT"})
place(LIB, "C1206", "CBULK", "100uF 6.3V", CX, 23.5, 0, "C15008", {1: "VCC", 2: "GND"})
for ref, (x, y), n in (("CDEC1", (CX - 7.0, 14.0), "VCC"), ("CDEC2", (CX - 7.0, 18.0), "VCC"),
                       ("CAVCC", (CX + 7.0, 18.0), "VCC"), ("CAREF", (CX + 7.0, 20.5), "AREF")):
    place(LIB, "C0603", ref, "100nF", x, y, 90, "C14663", {1: n, 2: "GND"})
place(LIB, "R0603", "RRST", "10k", CX - 7.0, 21.0, 90, "C25804", {1: "RESET", 2: "VCC"})

# ---- mode button, ISP holes (pin order TBD: this order is a placeholder), holes
place(LIB, "SW-SMD_L3.9-W3.0-P4.45", "SWMODE", "TS-1088-AR02016", CX, 67.0, 0, "C720477", {1: "MODE", 2: "GND"})
place(LIB, "HDR-TH_6P-P2.54-V-M-1", "JISP", "ISP (pin order TBD)", CX, 61.0, 0, "C37208",
      {1: "GND", 2: "VCC", 3: "RESET", 4: "SCK", 5: "MISO", 6: "MOSI"}, dnp=True)
for ref, y in (("H1", 3.5), ("H2", 78.5)):
    place(os.path.join(KICAD_FP, "MountingHole.pretty"), "MountingHole_3.2mm_M3", ref, "3.2mm hole", CX, y)

board.SetCopperLayerCount(2)
pcbnew.SaveBoard(OUT, board)
print("saved", OUT, "footprints:", len(board.GetFootprints()), "nets:", len(nets))
