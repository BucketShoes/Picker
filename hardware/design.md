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
| SW1–SW8 | 8 | Kinghelm KH-12X12X10H-SMT-D, 12×12 mm tactile, round plunger, 10 mm tall | C18186486 | Extended | 10,666 | Pure SMD, no peg holes. Used as the button itself, no cap. USD 0.06 |
| SWMODE | 1 | TS-1088-AR02016, 3.9×3 mm tactile | C720477 | Basic | 729,745 | Mode button in the middle |
| BAT1 | 1 | Lian Xin XDCR-2032-603, CR2032 SMD holder | C7498148 | Extended | 32,265 | Plastic hooks on one side; the metal contact on the other side pushes the cell into them and hooks over it too. USD 0.17 |
| LED1A/B–LED8A/B | 16 | KT-0603R red LED, 0603 | C2286 | Basic | 8.6 M | Two per button, one on each side between the switch's pads, so one shows past a finger from any side. Red runs from a coin cell to about 2.2 V; white and green don't |
| RL1A/B–RL8A/B | 16 | 220 Ω 0603 | C22962 | Basic | 2.7 M | One per LED (parallel LEDs sharing a resistor share current unevenly). About 4.5 mA each from a fresh cell, 9 mA per pin; firmware PWM dims |
| RRST | 1 | 10 kΩ 0603 | C25804 | Basic | 40 M | RESET pull-up |
| QBAT | 1 | AO3401A P-MOSFET, SOT-23 | C15127 | Basic | 1.06 M | Reverse-cell protection; gate tied to GND |
| CDEC1–CDEC4 | 4 | 100 nF 0603 | C14663 | Basic | 49 M | VCC ×2, AVCC, AREF |
| CBULK | 1 | 100 µF 6.3 V X5R 1206 | C15008 | Basic | 2.1 M | Covers LED current peaks that a coin cell can't |
| JISP | — | 6 plated holes in a straight row, 2.54 mm pitch | — | — | — | No part. Program by pushing a pin strip into the holes. Pin order to match your lead |

Extended part fees (about USD 3 each): **2**, the 12 mm switches and the holder. The MCU is Promotional, so no fee.

### Why these
- **Switch:** the C&K PTS125SK85PSMTR (C2835221) uses the same land pattern, but costs USD 0.28, has only 656 in stock, and has
  plastic locating pegs that need holes in the board. The Kinghelm part is pure SMD, its plunger is taller (10 mm against 8.5 mm),
  and it has 16× the stock. **Not yet checked:** the Kinghelm datasheet (plunger diameter, force, rated life).
- **Mode button:** the only two Basic tactile switches are small: the TS-1187A (5.1 mm square) and the TS-1088 (3.9 × 3 mm).
  Neither is a good main game button, but either works as a mode button.
- **Holder:** these retain the cell. The XDCR-2032-603 holds it with plastic hooks on one side and a hooked metal contact
  on the other, which pushes the cell into the hooks rather than out (read from the Lian Xin drawing, `Downloads\C7498148.pdf`).
  The similar Lian Xin BS-CR2032-8 (C7498149, USD 0.24, 13k in stock) probably works the same way, but its photos are too dark to tell.
  - **Metal straps** (MY-2032-16, C2902340, USD 0.08) also retain the cell, and use a copper pad on the board as the − contact.
  - **QIJEY C70373:** has through-holes and bottom-side pads.
- **MCU:** the 328P is Promotional (no extended fee) and has deep stock. Every 1- and 2-series ATtiny was either thin on stock or an extended fee.
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

- **Board:** about **43 × 89 mm** (3,830 mm²), 2-layer, 1.6 mm. Top: parts; bottom: GND pour, no parts.
- **Buttons:** 2 columns × 4 rows. Columns are 26 mm apart, rows 17 mm apart (5 mm between switch bodies).
  The board edge is just past the outer switch pads; nothing needs to extend beyond them.
- **LEDs:** two per button, one on each side, in the gap between that side's two switch pads (the pads are 5 mm apart).
  They sit just outside the switch body, so a finger on the plunger doesn't hide both, and they take no extra board area.
- **Middle strip** (between the columns, about 9 mm wide): the 6 ISP holes in a row, then U1, then the passives and QBAT,
  then the mode button.
- **End:** the holder lies across the board (31.5 mm of the 42 mm width), with the cell going in from the side or the top.
- **Silkscreen:** seat numbers by each button, cell polarity, ISP pin names and "Remove cell to program".
- **Bottom:** flat. No parts. Vias tented. Positions for 4 stick-on feet marked in silkscreen.
- **Seat numbering:** with a 2 × 4 grid, which button is "next" around the table is set in firmware. The default goes round
  the outside: down one column and up the other.

## Open
1. The ISP pin order of your lead (which signal goes in which of the 6 holes).
2. Holder: the XDCR-2032-603, or the BS-CR2032-8?

**Checked:** the KH switch's EasyEDA land has its pads at x ±7.0, y ±2.5 mm, each 2.54 × 1.4 mm, so each side has a 3.6 mm gap
between its two pads. A rotated 0603 LED (land about 2.6 mm long) fits with about 0.5 mm clearance each way, which is inside JLC's chip spacing.
The outer pads reach 8.27 mm from the switch centre, so the board is about **43 mm** wide rather than 42.
