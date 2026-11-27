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
| SW1–SW8 | 8 | BZCN TSF002A05026A, 12×12 mm tactile, 260 gf, 5.0 mm tall (plunger 1.8 mm above the rim, 1.25 mm above the corner domes), 6.8 mm plunger, ≥ 30,000 cycles | C2888710 | Extended | 652 | USD 0.033. Every field of the part number is decoded by its datasheet. Packed loose (code A): check JLC will place it |
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
- **Chosen:** TSF002A05026A (C2888710), same land as the 5.5 mm C2888711 it replaced (too pointy). TSF002B05030AL (C53243731) was dropped: its datasheet (the TSF002 family spec) lists force codes 18 and 26 only,
  so its "30" (300 gf) rests on JLC's listing alone, and the trailing "L" sits in a field the datasheet calls a special code, "not normally used", without defining it.
- **EasyEDA land vs datasheet:** EasyEDA's land is larger (pads 3.0 × 1.7 mm, 18 mm across) than BZCN's drawing (2.0 × 1.5 mm, 16.5 mm across).
  Kept per the all-EasyEDA rule; it covers the datasheet land.
- **EasyEDA 3D model is wrong:** it's a 7.35 mm square-stem switch, not this 5.5 mm round-plunger part. (The earlier C53243731's EasyEDA model
  was 4.5 mm tall for a 5.0 mm part, so it was off too.)
- **HAND-MADE 3D models** (asked for, Nov 2026): `pcb/lib/handmade.3dshapes/HANDMADE_TSF002A0<HH>26A.wrl` for H 4.3, 4.5, 5.0 and 5.5,
  made by `pcb/tools/make_switch_model.py` from the BZCN drawing. Body and top are the same for every height; only the plunger length changes.
  - **Dimensioned on the drawing:** 12 × 12 body, 3.2 mm to the top of the rim, 0.3 mm stand-off, plunger Ø6.8, legs 1.0 × 0.3 at 5 mm pitch, 15.0 mm tip to tip.
  - **Scaled off the drawing** (about 22 px/mm against the 12 mm body): rim about 0.95 wide around an inset metal plate with a Ø7.2 opening;
    four domes about Ø1.75 at ±4.05, their tops about 0.55 mm above the rim; plunger top face about Ø6.3 with a rounded edge.
  - **Guessed:** the plate sits 0.22 mm below the rim; the dome and edge profiles; the leg bend shape.
  - Colours from the drawing's parts table: black PPA body and plunger, tin-plated plate, silver legs. Matches LCSC's product photos by eye.
  - Check against a real switch when one arrives. JLC's own viewer still shows EasyEDA's model.
- **Plunger height** above the rim is H − 3.2: 1.1 (H 4.3), 1.3 (4.5), 1.8 (5.0), 2.3 (5.5); above the dome tops it is 0.55 less.
  Side by side: [`pcb/render-switch-heights.png`](pcb/render-switch-heights.png), [`pcb/render-switch-heights-side.png`](pcb/render-switch-heights-side.png).
  Same family at JLC, all 260 gf, Extended (JLC API, 26 Nov 2026):

  | H | Part | C-number | Stock | USD at 200 | EasyEDA land |
  |---|---|---|---|---|---|
  | 4.3 | TSF002**B**04326A (100k cycles) | C2888833 | 375 | 0.036 (at 100) | not checked; listing omits "gull wing" |
  | 4.5 | TSF002A04526A | C2888709 | 1,808 | 0.026 | `SW-SMD_4P-...-LS15.1`: pads 2.54 × 1.4 at ±7.0 (16.5 across, matches BZCN's land); a different footprint from the board's |
  | 5.0 | TSF002A05026A (**on the board**) | C2888710 | 652 | 0.027 | `KEY-SMD_4P-...-LS15.0` |
  | 5.5 | TSF002A05526A (was on the board) | C2888711 | 369 | 0.026 | `KEY-SMD_4P-...-LS15.0` |
  | 5.0 | TSF002B05026A (100k cycles) | C2888837 | 966 | 0.037 (at 100) | `LS15.1`, as for C2888709 |

  C2888709's EasyEDA model is 4.5 mm tall but its body is about 3.6 mm, so it isn't BZCN's shape either.
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

## Pin map (as on the board and in the schematic, 27 Nov 2026)

Pins are swappable within a category: what's fixed is the category, not which seat gets which pin, so routing may still swap them.
Seat n always means SWn, LEDnA/B, RLnA/B and the silkscreen number n; only the nets to U1 move. Pin numbers are TQFP-32.

**Categories** overlap on purpose: a pin is in every category it could serve, as "good" or "possible but undesirable".
Overlaps are resolved first, then rotation, then swaps within a category for routing.
- **PWM (LEDs):** good: PD0 (30), PD1 (31), PD2 (32), PD3 (1), PD5 (9), PD6 (10), PB1 (13), PB2 (14), all on the 328PB.
  Possible: PB3/MOSI (15, OC2A), undesirable since it's a programming pin. 8 LEDs need 8, so the 8 good pins are forced and decide themselves.
  Timers: 0 (PD6, PD5), 1 (PB1, PB2), 2 (PD3), 3 (PD0, PD2), 4 (PD1). On the 328P, PD0–PD2 have no PWM.
- **Button (needs a pull-up and a pin-change interrupt to wake):** good: every I/O pin, since every one has both. That is all of PB, PC0–PC5
  and PD, and on the 328PB also PE2/PE3 (19, 22). Possible but undesirable: MOSI, MISO, SCK (shared with programming).
  Not usable: RESET (only as I/O with a fuse that disables programming), ADC6/ADC7 on the 328P (analog only: no pull-up, no wake),
  pins 3 and 6 (tied to GND/VCC so either chip fits).
- **Analog:** ADC0–ADC5 (PC0–PC5, 23–28), ADC6 (19), ADC7 (22). Nothing needs one: the battery is measured against the internal
  1.1 V reference, with no pin.
- **Programming:** MOSI (15), MISO (16), SCK (17), RESET (29), fixed.
- **Power:** VCC 4 and 6 (pin 6 is PE1 on the 328PB), GND 3, 5, 21 (pin 3 is PE0 on the 328PB), AVCC 18, AREF 20.

Resolving the overlaps is trivial here: the 8 PWM pins go to the LEDs, and the 9 buttons take any 9 of the 11 remaining good I/O pins
(PB0, PB6, PB7, PC0–PC5, PD4, PD7), leaving the programming pins alone.

**U1 rotation: unchanged.** On this footprint pins 1–8 run along U1's bottom edge, 9–16 up its right edge, 17–24 right to left along the
top, 25–32 down its left edge. That already suits the board: the right edge (9–14) plus the bottom-right corner (7, 8) hold 4 PWM and
4 button pins, matching seats 1–4 on the right; the left edge (25–32) plus the bottom-left corner (1) hold 4 PWM and 4 button pins for
seats 5–8 on the left; the top edge has PC0 right under the mode button and AVCC/AREF by their caps; the bottom edge has VCC/GND
towards CBULK and the holder. Rotating 180° would put the mode-button pins at the bottom, away from the button.

**Assignment:** nearest first, keeping each category's pins in the same top-to-bottom order as the seats they go to, so tracks
within a category don't cross.

| Seat | Position | LED | Button |
|---|---|---|---|
| 1 | top right | PB2 (14) | PB0 (12) |
| 2 | right, upper | PB1 (13) | PD7 (11) |
| 3 | right, lower | PD6 (10) | PB7 (8) |
| 4 | bottom right | PD5 (9) | PB6 (7) |
| 5 | bottom left | PD3 (1) | PC5 (28) |
| 6 | left, lower | PD2 (32) | PC4 (27) |
| 7 | left, upper | PD1 (31) | PC3 (26) |
| 8 | top left | PD0 (30) | PC2 (25) |

- **Mode button:** PC0 (23), directly under the button.
- **ISP:** PB3 MOSI (15), PB4 MISO (16), PB5 SCK (17), PC6 RESET (29).
- **Spare:** PD4 (2), PC1 (24), ADC6 (19), ADC7 (22): no-connect flags in the schematic.
- **Firmware note:** Timer 0 drives seats 3 (PD6) and 4 (PD5), and also runs Arduino's millis(). At 1 MHz its default PWM is about 61 Hz;
  1 kHz or more at 1 MHz needs prescaler 1 (3.9 kHz; prescaler 8 gives only 488 Hz), which makes millis() run 64× fast unless
  firmware corrects it (at a 4 MHz clock, prescaler 8 gives 1.95 kHz). Timer 0 (and every timer
  but the watchdog) stops in power-down sleep anyway, so sleep timing uses the watchdog either way. A firmware-stage decision.
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
  Moved out from the switches for assembly margin (JLC's upload doesn't flag parts this close).
  - **Corners:** outer LEDs at the long edges, 4.6 mm along from the switch row towards the middle, next to the seat number.
    Inner LEDs beside the switch; the bottom two (4B, 5B) 1.5 mm further south to make room for the logo.
  - **Middle:** outer LEDs 7.5 mm from the switch centre, 4.7 mm towards the board's middle row; inner LEDs 7.8 mm from the centre,
    4.5 mm towards the nearer short edge, level with the holder ends, so players across the board see them (seat 2 is still hard to see from seats 5 and 6).
- **Numbers:** 1–8 in bold silkscreen, 4–5 mm tall at the long edges next to each seat's outer LED, reading from that side.
  **Clockwise from the top right:** right column top to bottom 1–4, left column bottom to top 5–8 (most games pass clockwise).
- **No reference designators on the silkscreen** (all hidden); "Remove cell to program" either side of the holder's bottom contact.
- **Middle strip**, top to bottom: hole H1, the mode button (labelled MODE), U1 with QBAT, its capacitors and RESET pull-up, CBULK, the cell holder
  (centred on the board) with a 20 mm silkscreen circle showing the cell, the ISP holes (labels above), the small logo, hole H2.
- **Resistors:** each seat's pair side by side, lined up to take the track from the MCU (placed by the user in KiCad, right side mirrored from the left).
- **Branding:** the Exiles Gaming Club skull ([`art/exiles-logo.png`](art/exiles-logo.png)) in silkscreen, placed by `tools/silk_logo.py`: 48 mm tall on the back
  with the club name cut out of the skull (purple mask shows through); 12.6 mm tall on top between the ISP holes and H2 (skull only; the text is too fine).
- **Bottom:** flat. No parts, the big logo. Positions for 4 stick-on feet to be marked.

## KiCad files ([`pcb/`](pcb))
- `picker-box.kicad_pcb`: the board. Made by `tools/build_board.py` as a starting point; **the board file is now the source** (edited in KiCad since 26 Nov 2026). The build script no longer matches it.
- `lib/`: EasyEDA footprints and symbols (`PickerBox`). The 3D models aren't in git (unclear redistribution terms): run `tools/fetch_parts.py` to fetch them.
- `picker-box.kicad_sch`: the schematic, **now the netlist source**. Started by `tools/make_schematic.py` from the board's nets: one symbol
  per footprint, a net label on every pin (no wires), one row per seat. `kicad-cli pcb drc --schematic-parity` reports 0 footprint errors.
  ERC lists pin-type warnings only: EasyEDA's symbols mark most pins "unspecified". PDF: [`pcb/picker-box-schematic.pdf`](pcb/picker-box-schematic.pdf).
  From here on change nets in the schematic and use Update PCB from Schematic.
- **Routing (first pass, 27 Nov 2026):** autorouted by `tools/autoroute.py` (my own grid router, run with KiCad's Python; it
  wipes all tracks, vias and zones first, so only for starting over). 0.25 mm signal tracks, 0.3 mm VCC/VBAT/GND, 0.2 mm
  clearance, 0.6/0.3 mm vias, 0.5 mm to the edge, copper kept 3 mm from the mounting-hole centres.
  - GND is a pour on both sides. Every GND pad has its own via, and there's a 5 mm grid of stitching vias (kept off silkscreen).
  - Programming nets run on the bottom, dropping through under the chip body. Everything else is mostly on top.
  - Correct but autorouter-shaped: not symmetric, with some long detours (VCC especially). Tidy by hand in KiCad.
  - Copper picture: [`pcb/route-copper.png`](pcb/route-copper.png), drawn by `tools/plot_copper.py`. Red/orange = top,
    blue/cyan = bottom, orange = VCC, pink = VBAT, white dots = vias.
- **DRC** (`kicad-cli pcb drc --schematic-parity`): 0 unconnected, 0 clearance errors, 0 parity issues. It lists only silkscreen
  warnings (labels overlapping each other and copper), to tidy at layout.
- **Renders:** the main switches use the hand-made model; everything else is EasyEDA's.

## Open
1. 328P or 328PB: chosen at JLC's BOM step, no KiCad change (likely 328PB at qty 10).
2. Silkscreen tidy (reference labels overlap the numbers, the small logo and each other).
3. Programmer: an ESP32-C6 the user already has, wired on a breadboard to the ISP holes at 3.3 V (cell out). Either as a USB ISP bridge, or
   storing the image and flashing it itself (handy for updates on site). Firmware in PlatformIO or the Arduino IDE; decided at the firmware stage.
4. **Firmware framework (decided 27 Nov 2026):** Arduino core (MiniCore, which covers both the 328P and the 328PB) built with
   PlatformIO in VS Code, not the Arduino IDE. Sleep is done directly with avr-libc (`avr/sleep.h`, pin-change wake), which works
   fine alongside the Arduino core. If the Arduino core ever gets in the way of sleeping properly, drop to plain avr-gcc.
   - Baseline mode (must work hundreds of times and survive years on a shelf): wake on a press, pick once at least two buttons
     are held, 3 s after the last press (like the web version), then sleep after a short while.
   - Other games (e.g. Simon) may run at full power, but sleep when the game ends or after about 10 min idle.
5. **JLC dry run:** done 26 Nov (BOM and footprint preview checked). Since then the only BOM change is the switches
   C2888711 → C2888710, on the same land, and no footprint has changed. Re-check only if the BOM or footprints change.
