// Software PWM for the 8 seat LEDs: 6-bit bit-angle modulation on Timer 2, about 500 Hz, the same on the 328P and 328PB.
#pragma once
#include <stdint.h>

extern uint8_t led[8];   // duty per seat, 0 (off) to 63 (full)

void leds_start();       // Timer 2 on
void leds_stop();        // Timer 2 off, every LED off (for sleep)
void leds_show();        // publish led[] (takes effect at the next PWM frame, within 2 ms)
void leds_clear();       // all off, published
uint8_t gamma16(uint8_t level);   // perceived brightness 0..15 to duty 0..63
