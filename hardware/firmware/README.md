# Picker box firmware

Arduino (MiniCore) under PlatformIO, for the ATmega328PB or 328P on the picker board (`../pcb`). Sleep is done directly
with avr-libc. Design and pin map: [`../design.md`](../design.md).

```
pio run            # 328PB (default)
pio run -e 328p    # 328P
```

## What it does

- **Asleep** until any button is pressed (power-down, about 0.2 µA). The press that wakes it counts.
- **Turn picker**, always the mode it wakes in. Everyone holds their button; held seats glow. Once at least 2 are held,
  they breathe faster for 3 s; any press or release restarts the 3 s. Then a light runs round the held seats, slows, and
  stops on one. That seat flashes until everyone lets go (at least 10 s). Then a new round can start, or after 5 s with
  nothing held it sleeps.
- **MODE** (with no seat held) starts **Simon**: the board plays a sequence of seats and the table repeats it; it grows
  by one each round and speeds up. A wrong press or 5 s without one ends it: everything flashes, the right seat flashes,
  then the score (rounds completed: a lap per 8, then the rest as lit seats from seat 1). MODE leaves at any time. Either
  way it goes back to the picker, which sleeps when left alone.
- **Power-up** (cell in): one lap of the seats, which also checks every LED.
- **Stuck button** (in a pocket): one button held alone for a minute sends it to sleep with that button driven low
  (no pull-up current) and ignored, and the watchdog looks every 8 s (about 3 µA) until it is released. Any button
  still held when it goes to sleep is treated the same way.

## How

- **Clock:** 4 MHz, the internal 8 MHz RC divided by 2 at start-up (`board.cpp`), so the factory fuses work as they
  are (CKDIV8 makes it 1 MHz only until the code runs). 4 MHz is in spec down to 1.8 V.
- **LEDs:** software PWM on Timer 2 (6-bit bit-angle modulation, about 500 Hz), the same on both chips, so the 328PB's
  extra timers aren't needed. Duty 0-63 per seat (`led[]`, `gamma16()` for even brightness steps). A seat at full is
  about 8 mA from the cell (two LEDs); animations keep most seats dim.
- **Buttons:** polled every 4 ms, debounced over 4 samples. Arduino's `millis()` runs as usual (Timer 0).
- **Randomness:** the exact time (`micros()`) of every button change is stirred into the generator.
- **Pins:** all in `board.h`. If routing swaps pins within a category, only those tables change.

## Flashing

Over ISP (the JISP holes: GND VCC RST SCK MISO MOSI), cell out. The programmer (an ESP32-C6) isn't set up yet, so
`upload_protocol` isn't set. A factory-fresh chip runs at 1 MHz, so the first flash needs a slow ISP clock (avrdude `-B 8`
or slower). Fuses don't need changing (brown-out detection is off from the factory); `pio run -t fuses` writes MiniCore's
equivalent set.

## Ideas for more games

- MODE in the picker could first show the previous winner, then a second press for Simon.
- Dice: press your seat for a roll shown as lit seats (1-8), or a d6 count.
- Turn tracker: the current player's seat glows; they press it to pass to the next clockwise.
- Quiz buzzer: first press locks out the rest; MODE resets.
- Reaction game: all seats light at a random moment; fastest press wins, early presses are out.
- Hot potato: a light passes as each holder presses; when the hidden timer runs out, whoever has it loses.
- Low-battery warning: measure VCC against the internal 1.1 V reference on wake, blink if under about 2.4 V.
