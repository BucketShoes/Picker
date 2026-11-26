# Picker box: design (parts and general layout)

A round board with 8 buttons around the edge, each with a red LED. Players each hold a button; it picks who goes first.
Other modes (turn tracker, quiz buzzer, timers, Simon) are firmware only. Any button can be repurposed as a mode button.

Deliberately simple: no USB, no charger, no boost converter, no case. It runs from a CR2032 cell, all parts are SMD and on
the top side, so the bottom is flat copper and solder mask (stick-on rubber feet, nothing to scratch a table).

Status: **parts chosen, layout proposed, for review.** The netlist and KiCad files come after this is agreed; firmware comes last.

## Parts

Live JLC data, 2026-11-26. Prices are USD per unit at the lowest quantity break.

| Ref | Qty | Part | LCSC | JLC type | Stock | Price | Notes |
|---|---|---|---|---|---|---|---|
| U1 | 1 | ATmega328P-AU (TQFP-32) | C14877 | Promotional Extended (no fee) | 36,556 | 2.31 | 1.8–5.5 V; internal clock, no crystal |
| SW1–SW8 | 8 | Kinghelm KH-12X12X10H-SMT-D, 12×12 mm tactile, round plunger, 10 mm tall | C18186486 | Extended | 10,666 | 0.06 | Pure SMD, no peg holes. Used as the button itself, no cap |
| BAT1 | 1 | Lian Xin XDCR-2032-603, CR2032 SMD holder | C7498148 | Extended | 32,265 | 0.17 | Plastic slide-in holder with both contacts built in, so no bare copper contact under the cell |
| LED1–LED8 | 8 | KT-0603R red LED, 0603 | C2286 | Basic | 8.6 M | — | Red runs from a coin cell to about 2.2 V; white and green don't |
| RL1–RL8 | 8 | 220 Ω 0603 | C22962 | Basic | 2.7 M | — | About 4.5 mA from a fresh cell (a little bright); firmware PWM dims |
| RRST | 1 | 10 kΩ 0603 | C25804 | Basic | 40 M | — | RESET pull-up |
| QREV | 1 | AO3401A P-MOSFET, SOT-23 | C15127 | Basic | 1.06 M | — | Reverse-cell protection (a slide-in holder takes the cell either way up) |
| CDEC1–CDEC4 | 4 | 100 nF 0603 | C14663 | Basic | 49 M | — | VCC ×2, AVCC, AREF |
| CBULK | 1 | 100 µF 6.3 V X5R 1206 | C15008 | Basic | 2.1 M | — | Covers LED and piezo current peaks that a coin cell can't |
| BZ1 | 1 | Murata PKLCS1212E4001-R1 piezo, 12×12 SMD | C113159 | Extended | 3,201 | — | **Not fitted (DNP).** Pads for a later order or hand fitting |
| JISP | 1 | 2×3 2.54 mm SMD vertical pin header | C192301 | Extended | 10,598 | 0.04 | **Not fitted (DNP).** ISP pads; solder a header or hold one in place |

Extended part fees (about USD 3 each): **2**, the switches and the holder. The MCU is Promotional, so no fee. The DNP parts
aren't ordered, so they have no fee.

### Why these
- **Switch:** the C&K PTS125SK85PSMTR (C2835221) uses the same land pattern, but it costs USD 0.28, has 656 in stock, and has
  plastic locating pegs that need holes in the board. The Kinghelm part is pure SMD, its plunger is taller (10 mm against 8.5 mm), and it has 16× the stock.
  **Not yet checked:** the Kinghelm datasheet (plunger diameter, force, rated life).
- **Holder:** the MY-2032-16 (C2902340, USD 0.08) is an open retainer that uses a 10 mm copper pad on the board as the − contact,
  and its EasyEDA footprint puts solder paste on that pad, which would leave a blob under the cell. The QIJEY C70373 has
  through-holes and bottom-side pads. The XDCR-2032-603 has neither problem.
- **MCU:** the 328P is Promotional (no extended fee) and has deep stock. Every 1- and 2-series ATtiny was either thin on stock or an extended fee.

## Footprints and models

**All EasyEDA** (via easyeda2kicad, now installed). KiCad's built-in libraries don't have the switch or the holder,
and boards don't mix libraries. **No hand-made footprints or models are planned.** If one turns out to be needed, I'll say so first.

## Power

```
CR2032 + ──QREV (AO3401A: drain to cell +, source to VCC, gate to GND)── VCC ── U1, LEDs, piezo
CR2032 − ── GND
```
- **Reversed cell:** the FET stays off and its body diode blocks.
- **Normal cell:** the FET turns on (gate at −VCC) and drops only millivolts.
- **Programming:** an Arduino-as-ISP supplies 5 V on the header's VCC pin, and the FET conducts both ways once on, so 5 V would
  push current into the coin cell. **Take the cell out before programming.** The silkscreen will say so next to JISP.
  The 328P and the LEDs are fine at 5 V (about 14 mA per LED through 220 Ω).

## Pin map (proposed; fixed at the netlist stage)

Each seat is one LED pin next to one button pin, so every pair leaves the chip on the same side. Buttons close to GND and use internal
pull-ups. All pins have pin-change interrupts, so any button wakes the chip from power-down.

| Seat | LED | Button | TQFP pins | Chip side |
|---|---|---|---|---|
| 1 | PD3 | PD4 | 1, 2 | left |
| 2 | PB6 | PB7 | 7, 8 | left (XTAL pins, free with the internal clock) |
| 3 | PD5 | PD6 | 9, 10 | bottom |
| 4 | PD7 | PB0 | 11, 12 | bottom |
| 5 | PC0 | PC1 | 23, 24 | right |
| 6 | PC2 | PC3 | 25, 26 | top |
| 7 | PC4 | PC5 | 27, 28 | top |
| 8 | PD0 | PD1 | 30, 31 | top |

- **Piezo:** PB1 / PB2 (OC1A / OC1B). Timer 1 drives them in antiphase, for twice the swing of a single pin.
- **ISP:** PB3 MOSI, PB4 MISO, PB5 SCK, PC6 RESET. Nothing else is on those pins.
- **Spare:** PD2 (INT0), ADC6, ADC7.
- **Battery level:** measured from the internal 1.1 V reference against AVCC, so it needs no pin and no divider.

The order of the seats around the board may change at layout, to keep the tracks short. The firmware uses a table, so that costs nothing.

## General layout (proposed)

```
               SW (seat 8)       SW (seat 1)
                  ·LED              LED·
        SW (7)                                SW (2)
          LED·        [ JISP ]  [ U1 ]          ·LED
                   ┌─────────────────────┐
        SW (6)     │   BAT1 (CR2032)      │      SW (3)
          LED·     └─────────────────────┘      ·LED
                          [ BZ1 ]
        SW (5)                                SW (4)
                  ·LED              LED·
```

- **Board:** round, **100 mm diameter**, which stays within JLC's 100×100 mm price band. 2-layer, 1.6 mm. Top: parts; bottom: GND pour.
- **Buttons:** 8 switches spaced evenly (45°) on a **38 mm radius**. That puts their centres about 29 mm apart, finger room between them.
  Each switch is rotated so its pads lie along the edge of the board.
- **LEDs:** each one sits outward of its button, at about 46 mm radius, so the player sees it beside their finger, not under it.
- **Centre:** the space inside the switch pads is about 60 mm across.
  - The coin-cell holder (about 32 × 23 mm) goes in the middle, with the cell sliding in from one side.
  - U1 goes in the gap on one side of the holder, with the ISP header next to it, and the piezo pads on the other side.
- **Silkscreen:** seat numbers by each button, cell polarity, and "Remove cell to program" next to JISP.
- **Bottom:** flat. No parts, no through-hole leads. Vias are tented. Positions for 4 stick-on feet marked in silkscreen.

## Questions for review
1. Board size: is a 100 mm round board right, or should it be smaller (e.g. 80 mm, buttons closer together) or larger?
2. Should the LEDs go outward of each button (toward the player) or inward?
3. Should JISP be fitted (one more extended fee, about USD 3) so programming is plug-in, or left as pads?
4. Should the piezo pads stay, unfitted?
