"""Fetch the board's EasyEDA footprints, symbols and 3D models into hardware/pcb/lib.

    pip install easyeda2kicad
    python hardware/pcb/tools/fetch_parts.py

The 3D models (lib/PickerBox.3dshapes) are not in git because their redistribution terms are unclear;
this script fetches them. Model paths are rewritten to ${KIPRJMOD} so the project opens anywhere.
"""
import glob
import os
import subprocess
import sys

PARTS = {
    "C14877": "ATmega328P-AU",
    "C53243731": "BZCN TSF002B05030AL 12x12 tactile, 300 gf, 5.0 mm",
    "C720477": "TS-1088-AR02016 mode button",
    "C7498148": "XDCR-2032-603 CR2032 holder",
    "C2286": "KT-0603R red LED",
    "C22966": "270R 0603",
    "C25804": "10k 0603",
    "C15127": "AO3401A",
    "C14663": "100nF 0603",
    "C15008": "100uF 6.3V 1206",
    "C37208": "1x6 2.54 mm header (ISP holes, not fitted)",
}

lib_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib")
out = os.path.join(lib_dir, "PickerBox")
os.makedirs(lib_dir, exist_ok=True)
for lcsc, what in PARTS.items():
    print(lcsc, what)
    subprocess.run([sys.executable, "-m", "easyeda2kicad", "--full", f"--lcsc_id={lcsc}", "--output", out, "--overwrite"],
                   check=True, stdout=subprocess.DEVNULL)

abs_prefix = (out + ".3dshapes/").replace("\\", "/")
for fp in glob.glob(os.path.join(out + ".pretty", "*.kicad_mod")):
    t = open(fp, encoding="utf-8").read()
    t2 = t.replace(abs_prefix, "${KIPRJMOD}/lib/PickerBox.3dshapes/")
    if t2 != t:
        open(fp, "w", encoding="utf-8", newline="").write(t2)
print("done")
