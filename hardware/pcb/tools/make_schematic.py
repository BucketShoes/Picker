"""Generate picker-box.kicad_sch from the board's nets, and link the board's footprints to it.

    "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/pcb/tools/make_schematic.py

Run once, with KiCad closed, to start the schematic. Afterwards the schematic is the netlist's source: edit it in KiCad
and push changes to the board with Update PCB from Schematic. Running this again overwrites the schematic.

- One symbol per footprint, from the project library (lib/PickerBox.kicad_sym, matched by its "LCSC Part" field);
  the mounting holes use a minimal no-pin hole symbol.
- Every connected pin gets a net label at its tip (no wires); unconnected pins get no-connect flags.
- Each footprint's path is set to its symbol's UUID and its library ID to PickerBox:<name>, so
  `kicad-cli pcb drc --schematic-parity` can check the two agree.
The schematic is written in KiCad 6 syntax (the library's format) and then upgraded with `kicad-cli sch upgrade`.
"""
import os
import re
import subprocess
import uuid
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB_DIR = os.path.dirname(HERE)
BOARD = os.path.join(PCB_DIR, "picker-box.kicad_pcb")
SCH = os.path.join(PCB_DIR, "picker-box.kicad_sch")
SYMLIB = os.path.join(PCB_DIR, "lib", "PickerBox.kicad_sym")
KICAD_CLI = r"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
G = 2.54


# ---- minimal s-expression reader/writer
def parse(text):
    tokens = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text)
    stack = [[]]
    for t in tokens:
        if t == "(":
            stack.append([])
        elif t == ")":
            done = stack.pop()
            stack[-1].append(done)
        else:
            stack[-1].append(t)
    return stack[0][0]


def dump(x):
    if isinstance(x, list):
        return "(" + " ".join(dump(i) for i in x) + ")"
    return x


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def uq(s):
    return s[1:-1] if s.startswith('"') else s


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def new_uuid():
    return str(uuid.uuid4())


# ---- library symbols: name -> (sexpr, LCSC, pins[number] = (x, y, angle))
lib = parse(open(SYMLIB, encoding="utf-8").read())
symbols = {}
for s in find(lib, "symbol"):
    name = uq(s[1])
    lcsc = None
    for p in find(s, "property"):
        if uq(p[1]) == "LCSC Part":
            lcsc = uq(p[2])
    pins = {}
    for sub in find(s, "symbol"):
        for pin in find(sub, "pin"):
            at = find(pin, "at")[0]
            num = uq(find(pin, "number")[0][1])
            pins[num] = (float(at[1]), float(at[2]), int(float(at[3])) if len(at) > 3 else 0)
    symbols[name] = (s, lcsc, pins)
by_lcsc = {v[1]: k for k, v in symbols.items() if v[1]}

HOLE_SYMBOL = ['symbol', '"Mechanical:MountingHole"', ['pin_names', ['offset', '1.016']], ['in_bom', 'no'], ['on_board', 'yes'],
               ['property', '"Reference"', '"H"', ['id', '0'], ['at', '0', '5.08', '0'], ['effects', ['font', ['size', '1.27', '1.27']]]],
               ['property', '"Value"', '"MountingHole"', ['id', '1'], ['at', '0', '3.175', '0'], ['effects', ['font', ['size', '1.27', '1.27']]]],
               ['property', '"Footprint"', '""', ['id', '2'], ['at', '0', '0', '0'], ['effects', ['font', ['size', '1.27', '1.27']], 'hide']],
               ['property', '"Datasheet"', '""', ['id', '3'], ['at', '0', '0', '0'], ['effects', ['font', ['size', '1.27', '1.27']], 'hide']],
               ['symbol', '"MountingHole_0_1"',
                ['circle', ['center', '0', '0'], ['radius', '1.27'], ['stroke', ['width', '1.27']], ['fill', ['type', 'none']]]]]

# ---- board
board = pcbnew.LoadBoard(BOARD)
fps = sorted(board.GetFootprints(), key=lambda f: (re.sub(r"\d.*", "", f.GetReference()), f.GetReference()))
parts = []
for f in fps:
    ref = f.GetReference()
    fpname = f.GetFPID().GetLibItemName().wx_str()
    if fpname.startswith("MountingHole"):
        sym, libnick, lcsc = None, "MountingHole", None
    else:
        lcsc = f.GetFieldText("LCSC Part #")
        if ref.startswith("SW") and lcsc == "C2888710":
            sym = "TSF002A05026A"
        else:
            sym = by_lcsc[lcsc]
        libnick = "PickerBox"
    nets = {}
    for p in f.Pads():
        if p.GetNumber():
            nets.setdefault(p.GetNumber(), set()).add(p.GetNetname().removeprefix("/"))   # "/X" = local label X
    for k, v in nets.items():
        assert len(v) == 1, (ref, k, v)
    parts.append(dict(ref=ref, fp=f, sym=sym, lib=libnick, fpname=fpname, value=f.GetValue(), lcsc=lcsc,
                      nets={k: v.pop() for k, v in nets.items()}, dnp=f.IsDNP(), uuid=new_uuid()))

# ---- layout: U1 on its own on the left, everything else in a grid of cells, grouped by designator prefix
out_syms, out_labels, out_nc, instances = [], [], [], []
used_lib = {}
label_dir = {0: 180, 180: 0, 90: 270, 270: 90}   # library pin angle -> label angle pointing away from the body


def snap(v):
    return round(v / G) * G


def place(part, x, y):
    x, y = snap(x), snap(y)
    if part["sym"]:
        sexpr, _, pins = symbols[part["sym"]]
        lib_id = "PickerBox:" + part["sym"]
        used_lib[lib_id] = sexpr
    else:
        pins, lib_id = {}, "Mechanical:MountingHole"
        used_lib[lib_id] = None
    props = [("Reference", part["ref"], 0, (x, y - 5.08), False),
             ("Value", part["value"], 1, (x, y + 5.08), False),
             ("Footprint", f'{part["lib"]}:{part["fpname"]}', 2, (x, y), True),
             ("Datasheet", "", 3, (x, y), True)]
    if part["lcsc"]:
        props.append(("LCSC Part #", part["lcsc"], 4, (x, y), True))
    if part["sym"] and pins:
        ys = [py for _, py, _ in pins.values()]
        props[0] = ("Reference", part["ref"], 0, (x, y - max(ys) - 2.54), False)
        props[1] = ("Value", part["value"], 1, (x, y - min(ys) + 2.54), False)
    node = ["symbol", ["lib_id", q(lib_id)], ["at", f"{x:g}", f"{y:g}", "0"], ["unit", "1"],
            ["in_bom", "no" if part["dnp"] or not part["lcsc"] else "yes"], ["on_board", "yes"], ["uuid", part["uuid"]]]
    for name, val, pid, (px, py), hide in props:
        eff = ["effects", ["font", ["size", "1.27", "1.27"]]] + (["hide"] if hide else [])
        node.append(["property", q(name), q(val), ["id", str(pid)], ["at", f"{px:g}", f"{py:g}", "0"], eff])
    for num, (px, py, ang) in sorted(pins.items(), key=lambda kv: kv[0]):
        node.append(["pin", q(num), ["uuid", new_uuid()]])
        tx, ty = x + px, y - py            # library y is up, schematic y is down
        net = part["nets"].get(num, "")
        if net:
            la = label_dir[ang % 360]
            just = ["justify", "right", "bottom"] if la in (180, 270) else ["justify", "left", "bottom"]
            out_labels.append(["label", q(net), ["at", f"{tx:g}", f"{ty:g}", str(la)],
                               ["effects", ["font", ["size", "1.27", "1.27"]], just], ["uuid", new_uuid()]])
        else:
            out_nc.append(["no_connect", ["at", f"{tx:g}", f"{ty:g}"], ["uuid", new_uuid()]])
    out_syms.append(node)
    instances.append(["path", q("/" + part["uuid"]), ["reference", q(part["ref"])], ["unit", "1"],
                      ["value", q(part["value"])], ["footprint", q(f'{part["lib"]}:{part["fpname"]}')]])


by_ref = {p["ref"]: p for p in parts}
place(by_ref.pop("U1"), 60.96, 101.6)
# one row per seat: switch, outer LED, inner LED, their resistors
for s in range(1, 9):
    y = 33.02 + (s - 1) * 22.86
    for col, ref in enumerate((f"SW{s}", f"LED{s}A", f"RL{s}A", f"LED{s}B", f"RL{s}B")):
        place(by_ref.pop(ref), 132.08 + col * 30.48, y)
# everything else in a block to the right
for i, ref in enumerate(sorted(by_ref)):
    place(by_ref[ref], 304.8 + (i % 3) * 33.02, 33.02 + (i // 3) * 27.94)

lib_syms = []
for lib_id, sexpr in used_lib.items():
    if sexpr is None:
        lib_syms.append(HOLE_SYMBOL)
    else:
        s = list(sexpr)
        s[1] = q(lib_id)
        lib_syms.append(s)

sheet_uuid = new_uuid()
sch = ["kicad_sch", ["version", "20211123"], ["generator", "eeschema"], ["uuid", sheet_uuid], ["paper", '"A3"'],
       ["title_block", ["title", '"Picker box"'], ["rev", '"1"'],
        ["comment", "1", '"Started by tools/make_schematic.py"']],
       ["lib_symbols"] + lib_syms] + out_nc + out_labels + out_syms + \
      [["sheet_instances", ["path", '"/"', ["page", '"1"']]], ["symbol_instances"] + instances]
open(SCH, "w", encoding="utf-8", newline="\n").write(dump(sch) + "\n")
r = subprocess.run([KICAD_CLI, "sch", "upgrade", "--force", SCH], capture_output=True, text=True)
print("upgrade:", r.returncode, (r.stdout + r.stderr).strip()[-300:])

# JISP is not fitted: mark the symbol DNP as on the board (KiCad 6 syntax had no DNP)
t = open(SCH, encoding="utf-8").read()
for p in parts:
    if p["dnp"]:
        i = t.index(p["uuid"])
        j = t.rindex("(dnp no)", 0, i)
        t = t[:j] + "(dnp yes)" + t[j + len("(dnp no)"):]
open(SCH, "w", encoding="utf-8", newline="").write(t)

# ---- link the board to the schematic
for p in parts:
    f = p["fp"]
    f.SetPath(pcbnew.KIID_PATH("/" + p["uuid"]))
    f.SetFPID(pcbnew.LIB_ID(p["lib"], p["fpname"]))
board.Save(BOARD)
# a local label X names the net "/X"; give the board's pads the same names (Update PCB from Schematic would)
t = open(BOARD, encoding="utf-8").read()
t = re.sub(r'\(net "([^"/][^"]*)"\)', r'(net "/\1")', t)
open(BOARD, "w", encoding="utf-8", newline="").write(t)
print(f"schematic: {len(out_syms)} symbols, {len(out_labels)} labels, {len(out_nc)} no-connects")
