// Pin map, as on the board (hardware/design.md, "Pin map"). Seat n is index n-1, clockwise from the top right.
// Routing may still swap pins within a category: only these tables change.
#pragma once
#include <avr/io.h>
#include <stdint.h>

#define SEATS 8
#define MODE_BIT (1u << 8)    // bit 8 of a button mask; bits 0-7 are the seats
#define SEAT_BITS 0xFFu

// LEDs sink: anode to VCC, cathode through 270 R to the pin, so a low pin lights both LEDs of that seat.
// One entry per seat: its bit on PORTB or PORTD (0 = not on that port).
static const uint8_t LED_B[SEATS] = {_BV(PB2), _BV(PB1), 0, 0, 0, 0, 0, 0};
static const uint8_t LED_D[SEATS] = {0, 0, _BV(PD6), _BV(PD5), _BV(PD3), _BV(PD2), _BV(PD1), _BV(PD0)};
#define LED_PB (_BV(PB2) | _BV(PB1))
#define LED_PD (_BV(PD6) | _BV(PD5) | _BV(PD3) | _BV(PD2) | _BV(PD1) | _BV(PD0))

// Buttons to GND with the internal pull-up. Index 8 is MODE.
static const uint8_t BTN_B[SEATS + 1] = {_BV(PB0), 0, _BV(PB7), _BV(PB6), 0, 0, 0, 0, 0};
static const uint8_t BTN_C[SEATS + 1] = {0, 0, 0, 0, _BV(PC5), _BV(PC4), _BV(PC3), _BV(PC2), _BV(PC0)};
static const uint8_t BTN_D[SEATS + 1] = {0, _BV(PD7), 0, 0, 0, 0, 0, 0, 0};
#define BTN_PB (_BV(PB0) | _BV(PB7) | _BV(PB6))
#define BTN_PC (_BV(PC5) | _BV(PC4) | _BV(PC3) | _BV(PC2) | _BV(PC0))
#define BTN_PD (_BV(PD7))

// Every other I/O pin is an input with its pull-up on, so nothing floats in sleep:
// PB3-PB5 (ISP), PD4 and PC1 (spare). PC6 is RESET. On the 328PB, PE2/PE3 (spare) too, but never PE0/PE1:
// they are tied to GND and VCC so either chip fits, and a pull-up on PE0 would leak into GND.
#define PULL_PB (BTN_PB | _BV(PB3) | _BV(PB4) | _BV(PB5))
#define PULL_PC (BTN_PC | _BV(PC1))
#define PULL_PD (BTN_PD | _BV(PD4))

// Port values with every LED off: what the PWM writes, with lit LEDs' bits cleared.
#define IDLE_PB (PULL_PB | LED_PB)
#define IDLE_PD (PULL_PD | LED_PD)

void board_init();
uint16_t btn_raw();   // pressed buttons right now (no debounce)
void btn_port_masks(uint16_t m, uint8_t *b, uint8_t *c, uint8_t *d);
