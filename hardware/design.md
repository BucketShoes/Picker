# Picker box: design (parts and general layout)

A small board with 8 buttons around the edge, each with a red LED. Players each hold a button; it picks who goes first.
Other modes (turn tracker, quiz buzzer, timers, Simon) are firmware only. A small mode button sits in the middle.

Kept deliberately simple and cheap: no USB, no charger, no boost converter, no sound, no case. It runs from a CR2032. Every part is
SMD and on the top side, so the bottom is flat (stick-on rubber feet, nothing to scratch a table).

Status: **parts and general layout, for review.** The netlist and KiCad files come after this is agreed; firmware comes last.

## Parts

Live JLC data, 2026-11-26. Prices are USD per unit at the lowest quantity break.

| Ref | Qty | Part | LCSC | JLC type | Stock | Notes |
|---|---|---|---|---|---|---|
| U1 | 1 | ATmega328P-AU (TQFP-32) | C14877 | Promotional Extended (no fee) | 36,556 | 1.8–5.5 V; internal clock, no crystal. USD 2.31 |
| SW1–SW8 | 8 | XKB TS-1103S-C-x, 12×12 mm tactile, 260 gf, round 6.8 mm plunger; height to pick (e.g. -C-H 7.5 mm, C561244) | C561244 (for -C-H) | Extended | 2,740 (-C-H) | Pure SMD. Used as the button itself, no cap. USD 0.08 at 50. Body 3.3 mm, so the plunger stands H − 3.3 mm proud |
| SWMODE | 1 | TS-1088-AR02016, 3.9×3 mm tactile | C720477 | Basic | 729,745 | Mode button in the middle |
| BAT1 | 1 | Lian Xin XDCR-2032-603, CR2032 SMD holder (top-loading) | C7498148 | Extended | 32,265 | **Chosen.** Plastic hooks on one side; the metal contact on the other side pushes the cell into them and hooks over it too. The + face sits a little recessed, which suits a pocket. USD 0.17 |
| LED1A/B–LED8A/B | 16 | KT-0603R red LED, 0603 | C2286 | Basic | 8.6 M | Two per button, one on each side between the switch's pads, so one shows past a finger from any side. Red runs from a coin cell to about 2.2 V; white and green don't |
| RL1A/B–RL8A/B | 16 | 100 Ω 0603 (Basic part to pick) | — | Basic | — | One per LED. Sized for the brightest we ever want (one seat flashing for a few seconds): about 8 mA per LED from a fresh cell, 16 mA per pin. Normal use dims with PWM |
| RRST | 1 | 10 kΩ 0603 | C25804 | Basic | 40 M | RESET pull-up |
| QBAT | 1 | AO3401A P-MOSFET, SOT-23 | C15127 | Basic | 1.06 M | Reverse-cell protection; gate tied to GND |
| CDEC1–CDEC4 | 4 | 100 nF 0603 | C14663 | Basic | 49 M | VCC ×2, AVCC, AREF |
| CBULK | 1 | 100 µF 6.3 V X5R 1206 | C15008 | Basic | 2.1 M | Covers LED current peaks that a coin cell can't |
| JISP | — | 6 plated holes in a straight row, 2.54 mm pitch | — | — | — | No part. Program by pushing a pin strip into the holes. Pin order to match your lead |

Extended part fees (about USD 3 each): **2**, the 12 mm switches and the holder. The MCU is Promotional, so no fee.

### Why these
- **Switch:** XKB's TS-1103S-C series states **260 gf** (code C; B is 160 gf), 200,000 cycles, 0.25 mm travel, a 3.3 mm body and a
  6.8 mm plunger, in heights 4.3–14 mm (drawing TS-1103S-C-H, rev A1). The Kinghelm KH-12X12 family lists 160 ± 30 and
  260 ± 50 gf without saying which part number is which, so its force is unknown; its body is also 3.3 mm. The XKB land is wider
  (18 mm across the pads), which the layout allows for.
  - **Plunger proud of the body** (H − 3.3 mm): 4.3 mm switch → 1.0 mm; 5.0 → 1.7; 6.0 → 2.7; 7.5 → 4.2; 8.0 → 4.7.
  - **To decide from a render:** how far the plunger must stand out for a bare finger. A bigger flat top would need a separate snap-on cap
    (square-stem switches such as the TS-1103ST-C-B take one), which is a hand-fitted extra part.
- **Mode button force:** the TS-1088-AR02016 is listed at 1.6 N (about 163 gf).
- **Mode button:** the only two Basic tactile switches are small: the TS-1187A (5.1 mm square) and the TS-1088 (3.9 × 3 mm).
  Neither is a good main game button, but either works as a mode button.
- **Holder:** these retain the cell. The XDCR-2032-603 holds it with plastic hooks on one side and a hooked metal contact
  on the other, which pushes the cell into the hooks rather than out (read from the Lian Xin drawing, `Downloads\C7498148.pdf`).
  The similar Lian Xin BS-CR2032-8 (C7498149, USD 0.24, 13k in stock) probably works the same way, but its photos are too dark to tell.
  - **Metal straps** (MY-2032-16, C2902340, USD 0.08) also retain the cell, and use a copper pad on the board as the − contact.
  - **QIJEY C70373:** has through-holes and bottom-side pads.
- **MCU:** the 328P is Promotional (no extended fee), USD 2.00 each at 10. Every 1- and 2-series ATtiny was thin on stock or an extended fee.
  - **ATmega168PA** (C8728): USD 2.08 at 10 and Extended, so it costs more, not less.
  - **ATmega328PB** (C132230): USD 1.46 at 10, 3,153 in stock, Extended (one more fee, about USD 3). It saves about USD 0.54 a board,
    so it only pays at 6+ boards. It also has two extra 16-bit timers; if its pins allow, all 8 seats could get hardware PWM.
    **To check at the netlist stage** against its datasheet.
- **Left out on purpose:** a piezo (about USD 8 per order of 5) and a fitted ISP header.

## Footprints and models

**All EasyEDA** (via easyeda2kicad, installed). KiCad's built-in libraries don't have the switch or the holder, and boards don't
mix libraries. **No hand-made footprints or models are planned.** If one turns out to be needed, I'll say so first.
The ISP holes are 6 plain plated holes; I'll use a pin-header footprint from the same library.

## Power

```
CR2032 + ── QBAT drain ─┤ AO3401A ├─ source ── VCC ── U1, LEDs
                          gate ── GND
JISP VCC ── VCC (direct)
CR2032 − ── GND
```

- **Running from the cell:** the gate sits about 3 V below the source, so QBAT is fully on (still on at 2.2 V; its threshold
  is −1.3 V at most). The drop is a few mV. Nothing else draws from the cell while asleep.
- **Reversed cell:** QBAT stays off and its body diode blocks. (Holders where one contact touches both the top and the side of
  the cell short a reversed cell inside the holder; no circuit can prevent that.)
- **Programming: take the cell out first.** The programmer's VCC goes straight to the chip's VCC. With a cell in, QBAT would conduct
  backwards and the programmer would push current into the cell. The silkscreen says so by the ISP holes. It's a one-off at first
  programming, so no isolation circuit.
- **Why the cell can't simply stay in and power the chip:** a 3.6 V programmer against a 2.7 V cell puts 0.9 V across the
  chip's input protection diodes (rated VCC + 0.5 V), which then conduct and push current into the cell.

## Pin map (proposed; fixed at the netlist stage)

Each seat is one LED pin next to one button pin, so every pair leaves the chip on the same side. Buttons close to GND and use internal
pull-ups. All pins have pin-change interrupts, so any button wakes the chip from power-down.

| Seat | LED | Button | TQFP pins |
|---|---|---|---|
| 1 | PD3 | PD4 | 1, 2 |
| 2 | PB6 | PB7 | 7, 8 (XTAL pins, free with the internal clock) |
| 3 | PD5 | PD6 | 9, 10 |
| 4 | PD7 | PB0 | 11, 12 |
| 5 | PC0 | PC1 | 23, 24 |
| 6 | PC2 | PC3 | 25, 26 |
| 7 | PC4 | PC5 | 27, 28 |
| 8 | PD0 | PD1 | 30, 31 |

- **Mode button:** PD2 (INT0).
- **LEDs:** each LED pin drives its button's two LEDs, each through its own resistor (about 9 mA per pin from a fresh cell).
- **ISP:** PB3 MOSI, PB4 MISO, PB5 SCK, PC6 RESET. Nothing else is on those pins.
- **Spare:** PB1, PB2, ADC6, ADC7.
- **Battery level:** measured from the internal 1.1 V reference against AVCC, so it needs no pin and no divider.

The order of the seats around the board may change at layout, to keep the tracks short. The firmware uses a table, so that costs nothing.

## General layout (proposed)

See [`layout-sketch.svg`](layout-sketch.svg) (to scale; a sizing sketch, not a layout).

- **Board:** **53 × 84 mm**, so it still fits a 54 × 85.6 mm card slot (wallet or card holder) despite its thickness. 2-layer, 1.6 mm.
  Top: parts; bottom: GND pour, no parts.
- **Buttons:** 2 columns × 4 rows, rows 21.5 mm apart. Each switch is turned so its pads are above and below it; the board edge is
  just past the switch body.
- **LEDs:** two per button, one above and one below, in the gap between that side's pads (3.5 mm gap on the XKB land).
- **Numbers:** 1–8 in silkscreen beside each button, so it doubles as a d8 dice roller. Numbered round the outside, so seat order
  follows the table.
- **Middle strip** (about 28 mm between the columns), from the top edge down:
  - the **6 ISP holes along the top edge**, easy to reach;
  - the **cell holder right below them**, as a reminder to take the cell out before programming;
  - U1, then the passives and QBAT;
  - the mode button;
  - the club **logo** in silkscreen;
  - a **3.2 mm lanyard hole** near the bottom edge.
- **Silkscreen:** cell polarity, ISP pin names, "Remove cell to program", button numbers, logo.
- **Bottom:** flat. No parts. Vias tented. Positions for 4 stick-on feet marked in silkscreen.

## LED brightness and PWM
- **Resistor** sets the brightest we ever want; PWM dims everything else (turn tracker, several lit at once).
- **PWM at 1 kHz or more**, since 125 Hz flicker is visible. Options, to settle at the firmware stage:
  - the 328P at 4 MHz (safe down to 1.8 V) with binary-coded modulation in software: about 6-bit levels at 1 kHz;
  - the 328PB's extra timers giving hardware PWM on the seats, at any frequency and no CPU cost.
- **KT-0603R limits** (datasheet rev A.0): 25 mA DC, 60 mA peak (1/10 duty, 0.1 ms). Brightness is roughly proportional to current.
- **Running from a 5 V supply** would push about 27 mA per LED through 100 Ω, so the firmware must cap the PWM duty when it measures VCC above about 4 V.

## Open
1. Switch height (plunger protrusion), after a render.
2. ATmega328P or 328PB.
3. The ISP pin order of your lead.
4. The club logo artwork (as an image or SVG) for the silkscreen.
