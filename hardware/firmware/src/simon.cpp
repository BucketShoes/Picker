// Simon on the 8 seats: the board plays a sequence, the table repeats it (anyone can press), one step longer each round.
// A wrong press or 5 s without one ends it: everything flashes, the right seat flashes, then the score shows.
// MODE leaves at any time. Either way it returns to the turn picker.
#include <Arduino.h>
#include "board.h"
#include "buttons.h"
#include "games.h"
#include "leds.h"

static const uint16_t INPUT_TIMEOUT_MS = 5000;
static const uint8_t MAX_LEN = 64;

static void light(uint8_t s, uint8_t level) {
    leds_clear();
    led[s] = level;
    leds_show();
}

// Next seat pressed (0-7), -1 on timeout, -2 for MODE.
static int8_t wait_press() {
    uint32_t t0 = millis();
    take_presses();
    for (;;) {
        service();
        uint16_t p = take_presses();
        if (p & MODE_BIT)
            return -2;
        if (p & SEAT_BITS)
            return __builtin_ctz(p & SEAT_BITS);
        if (millis() - t0 >= INPUT_TIMEOUT_MS)
            return -1;
    }
}

static bool mode_pressed() { return take_presses() & MODE_BIT; }

static void flash_all(uint8_t times) {
    for (uint8_t i = 0; i < times; i++) {
        for (uint8_t s = 0; s < SEATS; s++)
            led[s] = gamma16(9);
        leds_show();
        wait_ms(120);
        leds_clear();
        wait_ms(120);
    }
}

// Score = completed rounds: a lap per 8, then the rest as lit seats from seat 1.
static void show_score(uint8_t score) {
    for (uint8_t i = 0; i < score / 8; i++)
        spin(gamma16(10), 70);
    uint8_t rest = score % 8;
    if (!rest)
        return;
    for (uint8_t s = 0; s < rest; s++) {
        led[s] = gamma16(9);
        leds_show();
        wait_ms(150);
    }
    wait_ms(2500);
    leds_clear();
}

static void game_over(uint8_t right, uint8_t score) {
    leds_clear();
    wait_ms(200);
    flash_all(3);
    for (uint8_t i = 0; i < 3; i++) {
        light(right, gamma16(14));
        wait_ms(300);
        leds_clear();
        wait_ms(200);
    }
    wait_ms(400);
    show_score(score);
}

void simon_run() {
    static uint8_t seq[MAX_LEN];
    uint8_t len = 0;
    spin(gamma16(10), 50);
    spin(gamma16(10), 50);
    wait_ms(500);
    take_presses();

    for (;;) {
        seq[len++] = rng_below(SEATS);
        uint16_t on = len < 20 ? 480 - 14 * len : 200;   // speeds up as it gets longer
        for (uint8_t i = 0; i < len; i++) {
            light(seq[i], gamma16(14));
            wait_ms(on);
            leds_clear();
            wait_ms(on / 3);
            if (mode_pressed())
                return;
        }
        for (uint8_t i = 0; i < len; i++) {
            int8_t s = wait_press();
            if (s == -2) {
                leds_clear();
                return;
            }
            if (s < 0 || s != seq[i]) {
                game_over(seq[i], len - 1);
                return;
            }
            light(s, gamma16(14));          // lit while held (at least 150 ms, at most 1 s)
            uint32_t t0 = millis();
            while (millis() - t0 < 1000 && ((held() >> s) & 1 || millis() - t0 < 150))
                service();
            leds_clear();
        }
        if (len == MAX_LEN) {               // won: three fast laps
            for (uint8_t i = 0; i < 3; i++)
                spin(gamma16(15), 40);
            show_score(len);
            return;
        }
        wait_ms(700);
    }
}
