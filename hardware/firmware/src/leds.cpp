// Bit-angle modulation: each frame shows the duty's bit 5 for 32 time units, bit 4 for 16, ... bit 0 for 1, writing whole
// port bytes, so 8 LEDs cost 5 short interrupts per frame. A unit is one Timer 2 count (clk/128 = 32 us at 4 MHz); a
// frame is 63 units, 2.0 ms (about 500 Hz).
//
// Timer 2 runs free and each interrupt moves OCR2A on by the next interval, so timing doesn't drift with interrupt
// latency. Bit 0 (one unit) is too short to schedule safely behind Arduino's Timer 0 interrupt, so the bit-1 interrupt
// shows bit 0 first, waits it out, then shows bit 1.
#include <avr/interrupt.h>
#include <avr/sleep.h>
#include <util/delay.h>
#include "board.h"
#include "leds.h"

uint8_t led[8];

// Port patterns per bit, index 0..5 = bit 5..0. Two copies: the interrupt reads `front`, leds_show() writes the other.
static volatile uint8_t pat_b[2][6], pat_d[2][6];
static volatile uint8_t front, swap_req, running;
static uint8_t step;   // interrupt: 0..4

static const uint8_t DUR[5] = {32, 16, 8, 4, 1 + 2};   // the last step is bit 0 then bit 1

ISR(TIMER2_COMPA_vect) {
    uint8_t s = step;
    if (s == 0 && swap_req) {
        front ^= 1;
        swap_req = 0;
    }
    uint8_t f = front;
    if (s < 4) {
        PORTB = pat_b[f][s];
        PORTD = pat_d[f][s];
        step = s + 1;
    } else {
        PORTB = pat_b[f][5];   // bit 0
        PORTD = pat_d[f][5];
        _delay_us(28);         // one unit (32 us) less the time to get here
        PORTB = pat_b[f][4];   // bit 1
        PORTD = pat_d[f][4];
        step = 0;
    }
    OCR2A += DUR[s];
}

void leds_show() {
    while (swap_req && running) {   // the previous frame hasn't been taken yet: idle until the next interrupt
        set_sleep_mode(SLEEP_MODE_IDLE);
        sleep_mode();
    }
    uint8_t back = front ^ 1;
    for (uint8_t i = 0; i < 6; i++) {
        uint8_t mask = 0x20 >> i, b = IDLE_PB, d = IDLE_PD;
        for (uint8_t s = 0; s < 8; s++)
            if (led[s] & mask) {
                b &= ~LED_B[s];
                d &= ~LED_D[s];
            }
        pat_b[back][i] = b;
        pat_d[back][i] = d;
    }
    if (running)
        swap_req = 1;
    else
        front = back;
}

void leds_clear() {
    for (uint8_t s = 0; s < 8; s++)
        led[s] = 0;
    leds_show();
}

void leds_start() {
    PORTB = IDLE_PB;
    PORTD = IDLE_PD;
    step = 0;
    TCCR2A = 0;                          // normal mode (Arduino's init() set phase-correct PWM)
    TCCR2B = _BV(CS22) | _BV(CS20);      // clk/128
    OCR2A = TCNT2 + 4;
    TIFR2 = _BV(OCF2A);
    running = 1;
    TIMSK2 = _BV(OCIE2A);
}

void leds_stop() {
    TIMSK2 = 0;
    TCCR2B = 0;
    running = 0;
    swap_req = 0;
    PORTB = IDLE_PB;
    PORTD = IDLE_PD;
}

uint8_t gamma16(uint8_t level) {
    static const uint8_t G[16] = {0, 1, 2, 3, 4, 6, 8, 10, 13, 16, 20, 25, 31, 38, 47, 63};
    return G[level > 15 ? 15 : level];
}
