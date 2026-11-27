#include <Arduino.h>
#include <avr/sleep.h>
#include "board.h"
#include "buttons.h"

static uint16_t stable, cand, ignored, edges;
static uint8_t same;
static uint32_t last_poll;

void buttons_reset(uint16_t ignore) {
    stable = cand = edges = 0;
    same = 0;
    ignored = ignore;
}

static void poll() {
    uint16_t r = btn_raw();
    if (r != cand) {          // still changing (or bouncing)
        cand = r;
        same = 0;
        rng_mix(micros());
        return;
    }
    if (same < 3) {           // needs 4 equal samples (12-16 ms)
        same++;
        return;
    }
    ignored &= r;             // an ignored button counts again once it has been released
    uint16_t now = r & ~ignored;
    edges |= now & ~stable;
    stable = now;
}

uint16_t held() { return stable; }

uint16_t take_presses() {
    uint16_t e = edges;
    edges = 0;
    return e;
}

void buttons_ignore_held() {
    ignored |= stable;
    stable = 0;
    edges = 0;
}

void service() {
    uint32_t t = millis();
    if (t - last_poll >= 4) {
        last_poll = t;
        poll();
    }
    set_sleep_mode(SLEEP_MODE_IDLE);   // the next timer interrupt (within 2 ms) wakes it
    sleep_mode();
}

void wait_ms(uint16_t ms) {
    uint32_t t0 = millis();
    while (millis() - t0 < ms)
        service();
}

static uint32_t rs = 0x9E3779B9u;

void rng_mix(uint32_t x) {
    rs = (rs ^ x) * 1664525u + 1013904223u;
}

static uint32_t rng() {   // xorshift32
    if (!rs)
        rs = 1;
    rs ^= rs << 13;
    rs ^= rs >> 17;
    rs ^= rs << 5;
    return rs;
}

uint8_t rng_below(uint8_t n) { return rng() % n; }
