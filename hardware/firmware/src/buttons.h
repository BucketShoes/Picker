// Debounced buttons (bits 0-7 seats, bit 8 MODE), polled every 4 ms from service().
#pragma once
#include <stdint.h>

void buttons_reset(uint16_t ignore);   // after waking: start from "nothing held"; `ignore` stays ignored until released
uint16_t held();                       // debounced, without ignored buttons
uint16_t take_presses();               // presses since the last call, then cleared
void buttons_ignore_held();            // ignore every button held now until it is released

void service();                        // poll buttons when due, then idle-sleep until the next interrupt
void wait_ms(uint16_t ms);             // service() for that long

// Random numbers, stirred by the exact timing of every button change.
void rng_mix(uint32_t x);
uint8_t rng_below(uint8_t n);
