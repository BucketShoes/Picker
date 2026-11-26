# Picker box: design (parts and general layout)

A business-card-sized board with 8 buttons down its long sides, each with two red LEDs. Players sit round it the way they sit
round the table and reach in. It picks who goes first; other modes (dice, turn tracker, quiz buzzer, timers, Simon) are
firmware only. Planned as a small run of handouts for the gaming club.

Kept deliberately simple and cheap: no USB, no charger, no boost, no sound, no case. It runs from a CR2032 and sleeps until a
button is pressed. Every part is SMD and on the top side, so the bottom is flat (stick-on feet, nothing to scratch a table).

Status: **parts and general layout, for review.** Netlist and KiCad files come next; firmware last. All prices are USD.

## Parts

Live JLC data, 2026-11-26. Prices per unit at the lowest break unless noted.

| Ref | Qty | Part | LCSC | JLC type | Stock | Notes |
|---|---|---|---|---|---|---|
| U1 | 1 | ATmega328PB-AU (TQFP-32) | C132230 | Extended | 3,153 | USD 1.46 at 10. 8 hardware PWM outputs off the ISP pins (see Pin map). Recommended over the 328P (C14877, Promotional, USD 2.00 at 10) |
| SW1–SW8 | 8 | 12×12 mm tactile, round 6.8 mm plunger, about 5–5.5 mm tall, 260–300 gf | see below | Extended | — | Used as the button itself, no cap |
| SWMODE | 1 | TS-1088-AR02016, 3.9×3 mm tactile, 1.6 N | C720477 | Basic | 715,648 | Mode button in the middle |
| BAT1 | 1 | Lian Xin XDCR-2032-603, CR2032 holder, top-loading | C7498148 | Extended | 32,265 | Plastic hooks one side, hooked metal contact the other. + face slightly recessed. USD 0.17 |
| LED1A/B–LED8A/B | 16 | KT-0603R red LED, 0603 | C2286 | Basic | 8.6 M | One outside and one inside each button, between its pads |
| RL1A/B–RL8A/B | 16 | 270 Ω 0603 (Basic part to pick) | — | Basic | — | One per LED. Sized so **any** firmware is safe at 5 V (see LED drive) |
| RRST | 1 | 10 kΩ 0603 | C25804 | Basic | 40 M | RESET pull-up |
| QBAT | 1 | AO3401A P-MOSFET, SOT-23 | C15127 | Basic | 1.06 M | Reverse-cell protection; gate tied to GND |
| CDEC1–CDEC3 | 3 | 100 nF 0603 | C14663 | Basic | 49 M | VCC, AVCC, AREF (the 328PB has one VCC pin) |
| CBULK | 1 | 100 µF 6.3 V X5R 1206 | C15008 | Basic | 2.1 M | Covers LED current peaks a coin cell can't |
| JISP | — | 6 plated holes in a row, 2.54 mm pitch | — | — | — | No part. Program by pushing a pin strip into the holes. Pin order to match your lead |
| H1, H2 | — | 3.2 mm plated holes | — | — | — | Lanyard and/or mounting |

Extended fees (about USD 3 each): **3** with the 328PB (switches, holder, MCU), 2 with the 328P.

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
- **Height** to be chosen from a render.

## Footprints and models

**All EasyEDA** (easyeda2kicad, installed). KiCad's built-in libraries don't cover the switches or the holder, and boards don't
mix libraries. **No hand-made footprints or models are planned.** If one turns out to be needed, I'll say so first.

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
- **PWM** at 1 kHz or more. On the 328PB all 8 seats get hardware PWM (Timers 0–4), so it costs no CPU.

## Pin map (proposed for the 328PB; fixed at the netlist stage)

| Seat | LED (hardware PWM) | Button |
|---|---|---|
| 1 | PD6 (OC0A) | PD7 |
| 2 | PD5 (OC0B) | PD4 |
| 3 | PB1 (OC1A) | PB0 |
| 4 | PB2 (OC1B) | PB6 |
| 5 | PD3 (OC2B) | PB7 |
| 6 | PD0 (OC3A) | PC0 |
| 7 | PD1 (OC4A) | PC1 |
| 8 | PD2 (OC3B) | PC2 |

- **Mode button:** PC3.
- **ISP:** PB3 MOSI, PB4 MISO, PB5 SCK, PC6 RESET. Nothing else on them. (UART1 is also on PB3/PB4, so debug serial can use the ISP holes.)
- **Spare:** PC4, PC5, PE0–PE3.
- **Wake:** every pin, PE included, has a pin-change interrupt, so any button wakes it.
- **Battery level:** the internal 1.1 V reference against AVCC; no pin needed.
- The seat-to-pin assignment will change at layout to keep tracks short; the firmware uses a table.

## Sleep and pocket behaviour

- **Normally asleep.** Any button press wakes it and that same press counts: holding a finger down starts the picker straight away.
- **A stuck button** (pressed in a pocket) would draw 60–150 µA through its internal pull-up (RPU 20–50 kΩ at 3 V), flattening the cell in months.
  So if one button stays down alone for about a minute with nothing else happening, the firmware drops that pin's pull-up, ignores it, and
  goes back to sleep, waking every 8 s or so on the watchdog (about 3.2 µA) to see whether it's been released. No separate pocket mode needed.

## General layout (proposed)

See [`layout-sketch.svg`](layout-sketch.svg) (to scale; a sizing sketch, not a layout).

- **Board:** **53 × 82 mm**, so it fits a 54 × 85.6 mm card slot despite its thickness. 2-layer, 1.6 mm, **purple** soldermask.
  JLC lists purple as a standard colour with no extra fee on most 2-layer orders ([JLC blog](https://jlcpcb.com/blog/pcb-solder-mask-colors-performance),
  [capabilities](https://jlcpcb.com/capabilities/Capabilities)); confirm in the dry-run quote.
- **Buttons:** 4 down each long side, rows 21 mm apart. Players sit along the long sides, like the table.
- **LEDs:** one on the outside of each button (towards its player) and one on the inside (towards the middle), each in the gap between that side's pads.
- **Numbers:** 1–8 in silkscreen, running round the outside, so seat order follows the table and it doubles as a d8.
- **Middle strip**, top to bottom: hole H1, mode button, passives, U1, cell holder, the ISP holes, hole H2.
  The ISP holes sit at the bottom edge with the cell directly above them.
- **Branding:** small logo on top, large logo and club text on the back. No space reserved; it fits wherever it ends up at the end.
- **Bottom:** flat. No parts. Vias tented. Positions for 4 stick-on feet marked in silkscreen.

## Open
1. Switch part and height (plunger protrusion), after a render.
2. ATmega328PB (recommended) or 328P.
3. The ISP pin order of your lead.
4. The club logo artwork and text.
