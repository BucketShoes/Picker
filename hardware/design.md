# Picker box: design (parts and general layout)

A business-card-sized board with 8 buttons down its long sides, each with two red LEDs. Players sit round it the way they sit
round the table and reach in. It picks who goes first; other modes (dice, turn tracker, quiz buzzer, timers, Simon) are
firmware only. Planned as a small run of handouts for the gaming club.

Kept deliberately simple and cheap: no USB, no charger, no boost, no sound, no case. It runs from a CR2032 and sleeps until a
button is pressed. Every part is SMD and on the top side, so the bottom is flat (stick-on feet, nothing to scratch a table).

Status: **first KiCad board** in [`pcb/`](pcb): every part placed with its EasyEDA footprint and 3D model, nets assigned as guidance, no tracks. Renders: [`pcb/render-top.png`](pcb/render-top.png), [`pcb/render-bottom.png`](pcb/render-bottom.png), [`pcb/render-angle.png`](pcb/render-angle.png), switch close-ups [`pcb/render-switch.png`](pcb/render-switch.png) and [`pcb/render-switch-side.png`](pcb/render-switch-side.png) (**hand-made switch model**, see below). Firmware last. All prices are USD.

## Parts

Live JLC data, 2026-11-26. Prices per unit at the lowest break unless noted.

| Ref | Qty | Part | LCSC | JLC type | Stock | Notes |
|---|---|---|---|---|---|---|
| U1 | 1 | ATmega328P-AU (TQFP-32) | C14877 | Promotional Extended | 36,556 | The board takes either chip with no KiCad change: pins 3 and 6 are wired GND and VCC, which on the 328PB are PE0/PE1 (firmware must leave them as inputs). Choose at JLC's BOM step by changing U1's part number to the 328PB (C132230, USD 1.46 at 10, Extended); likely 328PB at qty 10 |
| SW1–SW8 | 8 | BZCN TSF002A05526A, 12×12 mm tactile, 260 gf, 5.5 mm tall (plunger 2.3 mm proud), 6.8 mm plunger, ≥ 30,000 cycles | C2888711 | Extended | 369 | USD 0.033. Every field of the part number is decoded by its datasheet. Packed loose (code A): check JLC will place it |
| SWMODE | 1 | TS-1088-AR02016, 3.9×3 mm tactile, 1.6 N | C720477 | Basic | 715,648 | Mode button in the middle |
| BAT1 | 1 | Lian Xin XDCR-2032-603, CR2032 holder, top-loading | C7498148 | Extended | 32,265 | Plastic hooks one side, hooked metal contact the other. + face slightly recessed. USD 0.17 |
| LED1A/B–LED8A/B | 16 | KT-0603R red LED, 0603 | C2286 | Basic | 8.6 M | One outside and one inside each button, between its pads |
| RL1A/B–RL8A/B | 16 | 270 Ω 0603 | C22966 | Basic | 700,847 | One per LED. Sized so **any** firmware is safe at 5 V (see LED drive) |
| RRST | 1 | 10 kΩ 0603 | C25804 | Basic | 40 M | RESET pull-up |
| QBAT | 1 | AO3401A P-MOSFET, SOT-23 | C15127 | Basic | 1.06 M | Reverse-cell protection; gate tied to GND |
| CDEC1, CDEC2, CAVCC, CAREF | 4 | 100 nF 0603 | C14663 | Basic | 49 M | VCC ×2, AVCC, AREF (the 328PB has one VCC pin, so one fewer) |
| CBULK | 1 | 100 µF 6.3 V X5R 1206 | C15008 | Basic | 2.1 M | Covers LED current peaks a coin cell can't |
| JISP | — | 6 plated holes in a row, 2.54 mm pitch (footprint of header C37208, not fitted) | C37208 | — | — | Program by pushing a pin strip into the holes, wired to a breadboard programmer. Order GND, VCC, RST, SCK, MISO, MOSI (pin 1 square), every pin labelled in silkscreen |
| H1, H2 | — | 3.2 mm holes | — | — | — | Lanyard and/or mounting. KiCad's stock `MountingHole_3.2mm_M3` (no copper, no model): the one footprint not from EasyEDA, since a bare hole has no EasyEDA part |

Extended fees (about USD 3 each): **2** with the 328P (switches, holder), 3 with the 328PB. Promotional and Economic status only really shows at the ordering step.

### Switch candidates (all 12×12 SMD, all with a 6.8 mm round plunger)

| Part | LCSC | Force | Height (plunger proud) | Life | Land across pads | Stock | USD |
|---|---|---|---|---|---|---|---|
| BZCN TSF002**A055**26A | C2888711 | 260 gf | 5.5 mm (2.3 mm) | ≥ 30,000 | 16.5 mm | 369 | 0.033 |
| BZCN TSF002**B050**30AL | C53243731 | 300 gf (3 N, JLC listing) | 5.0 mm (1.8 mm) | ≥ 100,000 | 16.5 mm | 435 | 0.067 |
| XKB TS-1103S-**C**-C | C318916 | 260 gf | 5.0 mm (1.7 mm) | 200,000 | 18 mm | 709 | 0.10 |
| XKB TS-1103S-**C**-E | C318915 | 260 gf | 6.0 mm (2.7 mm) | 200,000 | 18 mm | 588 | 0.083 |
| XKB TS-1103S-**C**-H | C561244 | 260 gf | 7.5 mm (4.2 mm) | 200,000 | 18 mm | 2,740 | 0.099 |

- **Sources:** BZCN TSF002 drawing and spec (2021-06-01): body 3.2 mm, travel 0.30–0.35 mm, part number = life letter, height, force, packing.
  XKB TS-1103S-C-H drawing (rev A1): body 3.30 mm, travel 0.25 mm, code C = 260 gf, B = 160 gf.
- **Kinghelm KH-12X12** (the earlier pick): its datasheet lists 160 ± 30 and 260 ± 50 gf but not which part number is which, so it's out.
- **The narrower BZCN land** (16.5 mm) is what lets the board stay 53 mm wide with the cell between the columns.
- **BZCN packing code "A" means loose (bulk).** Check in the JLC dry run that they'll place it.
- **Force for reference:** both Basic tactiles (TS-1088, TS-1187A) are 1.6 N, about 163 gf. 260 gf is 1.6× that; 300 gf is 1.8×.
  For the same force a bigger plunger spreads it over more fingertip, so it feels less sharp, not lighter.
- **Bigger plunger tops:** every 12×12 datasheet read here (Kinghelm, XKB, BZCN) has a 6.0–6.8 mm plunger. A bigger flat top
  means a square-stem switch with a snap-on cap, which is a hand-fitted extra part.
- **Chosen:** TSF002A05526A (C2888711). TSF002B05030AL (C53243731) was dropped: its datasheet (the TSF002 family spec) lists force codes 18 and 26 only,
  so its "30" (300 gf) rests on JLC's listing alone, and the trailing "L" sits in a field the datasheet calls a special code, "not normally used", without defining it.
- **EasyEDA land vs datasheet:** EasyEDA's land is larger (pads 3.0 × 1.7 mm, 18 mm across) than BZCN's drawing (2.0 × 1.5 mm, 16.5 mm across).
  Kept per the all-EasyEDA rule; it covers the datasheet land.
- **EasyEDA 3D model is wrong:** it's a 7.35 mm square-stem switch, not this 5.5 mm round-plunger part. (The earlier C53243731's EasyEDA model
  was 4.5 mm tall for a 5.0 mm part, so it was off too.)
- **HAND-MADE 3D model** (asked for, Nov 2026): `pcb/lib/handmade.3dshapes/HANDMADE_TSF002A05526A.wrl`, made by `pcb/tools/make_switch_model.py`
  from the BZCN drawing. From the drawing: 12 × 12 body, 3.2 mm body height, H 5.5 mm, plunger Ø6.8 (2.3 mm proud), legs 1.0 × 0.3 at
  5 mm pitch, 15.0 mm tip to tip, black PPA body and plunger, tin-plated cover, silver legs. **Guessed** (not on the drawing): cover thickness 0.2,
  cover opening Ø7.2, corner posts Ø1.2 at ±4.6, the 0.3 mm plunger chamfer, 0.15 mm body stand-off, leg bend shape.
  Check against a real switch when one arrives. The board build script swaps it in for EasyEDA's; JLC's own viewer still shows EasyEDA's.
- **Contact rating vs reliability:** the 50 mA 12 V rating is the most it may switch, not a reliability figure. Life (100,000 cycles here) is mechanical wear.
  Whether it registers every press depends on contact resistance (≤ 100 mΩ) and the minimum load: BZCN rate it down to 1 V 10 µA, and a 20–50 kΩ
  pull-up at 3 V passes 60–150 µA, comfortably above that.

## Footprints and models

**All EasyEDA** (easyeda2kicad, installed). KiCad's built-in libraries don't cover the switches or the holder, and boards don't
mix libraries. No hand-made footprints. **One hand-made 3D model**, the main switch (above), made on request because EasyEDA's is a different part.

## Power

```
CR2032 + ── QBAT drain ─┤ AO3401A ├─ source ── VCC ── U1, LED anodes
                          gate ── GND
JISP VCC ── VCC (direct)
CR2032 − ── GND
```

- **On the cell:** QBAT is fully on (gate 3 V below the source; still on at 2.2 V), so the drop is a few mV.
- **Reversed cell:** QBAT stays off and its body diode blocks. (A holder contact touching both the top and side of a reversed cell
  shorts it inside the holder; no circuit can prevent that.)
- **Programming: take the cell out first.** Programmer VCC goes straight to VCC. The ISP holes sit right next to the holder as the reminder,
  and the silkscreen says so.
- **Sleep current:** 0.2 µA typical (328PB power-down, WDT off, 3 V, 25 °C; DS40001906C Table 33-3). 3.2 µA with the watchdog running.

## LED drive (5 V safe)

- **LEDs are driven by sinking:** anode to VCC, cathode through its resistor to the pin; a low pin lights it. The LED current then returns
  through the chip's two GND pins rather than its single VCC pin.
- **270 Ω per LED** keeps every limit even if firmware lights all 16 at once from a 5 V programmer:
  - about 10 mA per LED (LED rating 25 mA DC; KT-0603R datasheet rev A.0);
  - 20 mA per pin (rated 40 mA; test condition 20 mA at 5 V);
  - at most 80 mA per port group and per GND pin, with seats spread across groups (limits 100 mA each; DS40001906C Table 33-1 and page 407 notes).
- **From the cell** that gives about 4 mA per LED at full brightness (fresh cell), which is the brightest it ever gets. PWM dims the rest.
- **PWM** at 1 kHz or more. On the 328PB all 8 seats get hardware PWM (Timers 0–4), so it costs no CPU. On a 328P, seats 6–8 (PD0–PD2) need
  software PWM: a few brightness steps at 1 MHz, more if firmware raises the clock prescaler to 2–4 MHz (fine down to 1.8 V).

## Pin map (guidance; as on the board, fixed later)

Chosen so it also works on the 328PB with hardware PWM on every seat. Pin numbers are TQFP-32.

| Seat | LED (PWM on 328PB) | Button |
|---|---|---|
| 1 | PD6 (10) | PD7 (11) |
| 2 | PD5 (9) | PD4 (2) |
| 3 | PB1 (13) | PB0 (12) |
| 4 | PB2 (14) | PB6 (7) |
| 5 | PD3 (1) | PB7 (8) |
| 6 | PD0 (30) | PC0 (23) |
| 7 | PD1 (31) | PC1 (24) |
| 8 | PD2 (32) | PC2 (25) |

- **Mode button:** PC3 (26).
- **ISP:** PB3 MOSI (15), PB4 MISO (16), PB5 SCK (17), PC6 RESET (29).
- **Spare:** PC4, PC5, ADC6, ADC7.
- **Wake:** every I/O pin has a pin-change interrupt, so any button wakes it.
- **Battery level:** the internal 1.1 V reference against AVCC; no pin needed.
- **Nets on the board:** each seat's LED pin drives `LEDn`, which feeds two 270 Ω resistors to the two LED cathodes (`LEDnA_K` outside, `LEDnB_K` inside);
  LED anodes are on `VCC`. Switch pads 1–2 are `BTNn`, pads 3–4 `GND`.

## Sleep and pocket behaviour

- **Normally asleep.** Any button press wakes it and that same press counts: holding a finger down starts the picker straight away.
- **A stuck button** (pressed in a pocket) would draw 60–150 µA through its internal pull-up (RPU 20–50 kΩ at 3 V), flattening the cell in months.
  So if one button stays down alone for about a minute with nothing else happening, the firmware drops that pin's pull-up, ignores it, and
  goes back to sleep, waking every 8 s or so on the watchdog (about 3.2 µA) to see whether it's been released. No separate pocket mode needed.

## General layout (as on the first board)

- **Board:** **53 × 82 mm**, 3 mm corner radius, so it fits a 54 × 85.6 mm card slot. 2-layer, 1.6 mm, purple (chosen; same price as green). The board's stackup is set to purple so KiCad's 3D view matches.
  JLC lists purple as a standard colour with no extra fee on most 2-layer orders ([JLC blog](https://jlcpcb.com/blog/pcb-solder-mask-colors-performance),
  [capabilities](https://jlcpcb.com/capabilities/Capabilities)); confirm in the dry-run quote.
- **Buttons:** 4 down each long side, symmetric, the outer ones in the corners. Rows at 6.5, 29.5, 52.5, 75.5 mm from the top.
  - **Corner switches** sit 3 mm further in than the middle ones (centres 11.9 mm from the long edges), pads left and right.
  - **Middle switches** are turned 90° (pads top and bottom) so their wide land clears the cell holder.
- **LEDs:** one outside each button (towards its player) and one inside (towards the middle), clear of the switch legs.
  - **Corners:** 10 mm from the switch centre, just past the pad ends (the outer ones stayed where they were when the switches moved in).
  - **Middle:** 6.8 mm from the switch centre, against the plain sides of the turned switches. The inner ones sit 4.5 mm towards the nearer
    short edge, level with the holder ends, so players across the board see them (seat 2 is still hard to see from seats 5 and 6).
- **Numbers:** 1–8 in silkscreen, running round the outside: left column top to bottom 1–4, right column bottom to top 5–8.
- **Middle strip**, top to bottom: hole H1, U1 with QBAT, its capacitors and RESET pull-up, CBULK, the cell holder (centred on the board)
  with a 20 mm silkscreen circle showing the cell, the ISP holes (labelled), the mode button (labelled MODE, 2.5 mm lower to fit the labels), hole H2.
- **Resistors:** in the gaps between rows, next to their seat's number. Arrangement only; they'll move when routed.
- **Branding:** the Exiles Gaming Club skull ([`art/exiles-logo.png`](art/exiles-logo.png)) in silkscreen, generated by the build script: 48 mm tall on the back
  with the club name cut out of the skull (purple mask shows through), 5 mm tall on top between H1 and U1 (skull only; the text is too fine at that size).
- **Bottom:** flat. No parts, the big logo. Positions for 4 stick-on feet to be marked.

## KiCad files ([`pcb/`](pcb))
- `picker-box.kicad_pcb`: the board. Made by `tools/build_board.py` as a starting point; from now on the board file is the source, edited in KiCad.
- `lib/`: EasyEDA footprints and symbols (`PickerBox`). The 3D models aren't in git (unclear redistribution terms): run `tools/fetch_parts.py` to fetch them.
- No schematic yet; the nets on the board are the netlist for now.
- **DRC** (`kicad-cli pcb drc`): no part overlaps or copper clearance errors. It reports the 108 unrouted connections (expected) and
  silkscreen labels overlapping each other and pads (to tidy at layout).
- **Renders:** the main switches use the hand-made model; everything else is EasyEDA's.

## Open
1. 328P or 328PB: chosen at JLC's BOM step, no KiCad change (likely 328PB at qty 10).
2. Silkscreen tidy (reference labels overlap the numbers, the small logo and each other).
3. Programmer: an ESP32-C6 the user already has, wired on a breadboard to the ISP holes at 3.3 V (cell out). Either as a USB ISP bridge, or
   storing the image and flashing it itself (handy for updates on site). Firmware in PlatformIO or the Arduino IDE; decided at the firmware stage.
