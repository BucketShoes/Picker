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
| LED1–LED8 | 8 | KT-0603R red LED, 0603 | C2286 | Basic | 8.6 M | Red runs from a coin cell to about 2.2 V; white and green don't |
| RL1–RL8 | 8 | 220 Ω 0603 | C22962 | Basic | 2.7 M | About 4.5 mA from a fresh cell (a little bright); firmware PWM dims |
| RRST | 1 | 10 kΩ 0603 | C25804 | Basic | 40 M | RESET pull-up |
| QBAT | 1 | AO3401A P-MOSFET, SOT-23 | C15127 | Basic | 1.06 M | Reverse-cell protection and cell/programmer mutual exclusion, see Power |
| DPROG | 1 | BAT54C,215 (Nexperia) Schottky pair, SOT-23 | C37704 | Promotional (no fee) | 408,948 | Programmer feed; one half used. IR 2 µA max at 25 V |
| RGP | 1 | 1 kΩ 0603 | (Basic, to pick) | Basic | — | Programmer VCC to the QBAT gate |
| RGG | 1 | 10 kΩ 0603 | C25804 | Basic | — | QBAT gate to GND (same part as RRST) |
| CDEC1–CDEC4 | 4 | 100 nF 0603 | C14663 | Basic | 49 M | VCC ×2, AVCC, AREF |
| CBULK | 1 | 100 µF 6.3 V X5R 1206 | C15008 | Basic | 2.1 M | Covers LED current peaks that a coin cell can't |
| JISP | — | 6 plated holes in a straight row, 2.54 mm pitch | — | — | — | No part. Program by pushing a pin strip into the holes. Pin order to match your lead |

Extended part fees (about USD 3 each): **2**, the 12 mm switches and the holder. The MCU and the diode are Promotional, so no fee.

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

## Power: cell or programmer, never both

```
CR2032 + ── QBAT drain ─┤ AO3401A ├─ source ── VCC ── U1, LEDs
                          gate ── RGG 10k ── GND
                          gate ── RGP 1k ── VPROG
JISP VCC pin ── VPROG ── DPROG (BAT54C, anode → cathode) ── VCC
CR2032 − ── GND
```

- **Running from the cell** (no programmer): VPROG floats, and RGG pulls the gate to GND. QBAT is on at about 3 V gate drive
  (still on at 2.2 V; its threshold is −1.3 V at most), so the drop is a few mV.
- **Programmer attached** (3.3–5 V): VCC = VPROG − about 0.3 V through DPROG. The gate sits at VPROG × 10/11, which is within about 0.3 V of
  the source, so QBAT is off. Its body diode faces the cell, so nothing flows into the cell.
  - The ISP signals are then at most about 0.3 V above VCC, inside the 328P's "VCC + 0.5 V" limit.
  - With a 5 V programmer the gate sits about 0.2 V above the source. That's fine; the AO3401A's gate rating is ±12 V.
- **Reversed cell:** QBAT's body diode blocks and the FET stays off. Holders whose one contact touches both the top and the side of
  the cell short a reversed cell inside the holder. No circuit can prevent that, but the FET still protects the board
  wherever only reverse voltage reaches it.
- **Sleep current added:** DPROG's reverse leakage at 3 V, through RGP and RGG to GND. **Not yet checked:** the BAT54 datasheet's leakage
  curve at 3 V, to confirm it's in the tens of nA, not µA.
- **Why not program with the cell in, and no VCC pin:** a 3.6 V programmer and a 2.7 V cell give 0.9 V across the chip's input
  protection diodes, which then conduct and push current into the cell.

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
- **ISP:** PB3 MOSI, PB4 MISO, PB5 SCK, PC6 RESET. Nothing else is on those pins.
- **Spare:** PB1, PB2, ADC6, ADC7.
- **Battery level:** measured from the internal 1.1 V reference against AVCC, so it needs no pin and no divider.

The order of the seats around the board may change at layout, to keep the tracks short. The firmware uses a table, so that costs nothing.

## General layout (proposed)

See [`layout-sketch.svg`](layout-sketch.svg) (to scale; a sizing sketch, not a layout).

- **Board:** **70 × 90 mm** rounded rectangle, 2-layer, 1.6 mm. Smaller area keeps the stencil and board cost down.
  Top: parts; bottom: GND pour, no parts.
- **Buttons:** 8 switches inset 10 mm from the edge: one at each corner, one at the middle of each side. They're 25 mm apart
  across the board and 35 mm apart along it.
- **LEDs:** each one is 9 mm in from its button, toward the centre, so the player's finger doesn't cover it.
- **Centre:** the holder (16 × 31.5 mm, the cell overhangs to 20 mm wide) lies lengthwise in the middle.
  - Below it: U1, with the passives, QBAT and DPROG beside it.
  - Above it: the 6 ISP holes in a row, and the mode button.
- **Silkscreen:** seat numbers by each button, cell polarity, and the ISP pin names.
- **Bottom:** flat. No parts. Vias tented. Positions for 4 stick-on feet marked in silkscreen.
- **If smaller is wanted:** 64 × 84 mm probably still fits.

## Open
1. The ISP pin order of your lead (which signal goes in which of the 6 holes).
2. Holder: the XDCR-2032-603, or the BS-CR2032-8?
3. Board size: 70 × 90 mm, or try 64 × 84 mm?
