// Turn picker, as the web version: everyone holds their button; 3 s after the last press or release, with at least 2
// held, a light runs round the held seats, slows down and stops on one. That seat flashes until everyone lets go
// (at least 10 s), then it goes back to waiting, and to sleep after 5 s with nothing held.
#include <Arduino.h>
#include "board.h"
#include "buttons.h"
#include "games.h"
#include "leds.h"

static const uint16_t HOLD_MS = 3000;        // wait after the last change before picking
static const uint16_t SLEEP_EMPTY_MS = 5000; // nothing held
static const uint32_t SLEEP_ALONE_MS = 60000;// one button held on its own (likely stuck): sleep, treating it as stuck
static const uint16_t SHOW_MIN_MS = 10000;   // the winner shows for at least this long
static const uint32_t SHOW_MAX_MS = 60000;   // ...and until released, but no longer than this

void spin(uint8_t level, uint16_t step_ms) {
    for (uint8_t s = 0; s < SEATS; s++) {
        leds_clear();
        led[s] = level;
        leds_show();
        wait_ms(step_ms);
    }
    leds_clear();
}

static void draw_waiting(uint8_t h, uint8_t n, uint32_t since) {
    uint8_t lvl;
    if (n < 2) {
        lvl = gamma16(5);
    } else {   // breathe, faster as the pick gets near
        uint32_t t = millis(), e = t - since;
        if (e > HOLD_MS)
            e = HOLD_MS;
        uint16_t period = 900 - (uint16_t)e / 5;           // 900 ms down to 300 ms
        uint8_t ph = (uint8_t)((t % period) * 32 / period); // 0..31
        uint8_t tri = ph < 16 ? ph : 31 - ph;               // 0..15..0
        lvl = gamma16(4 + tri / 2);                         // levels 4..11
    }
    for (uint8_t s = 0; s < SEATS; s++)
        led[s] = (h >> s) & 1 ? lvl : 0;
    leds_show();
}

static uint8_t pick_and_show(uint8_t h) {
    uint8_t cand[SEATS], n = 0;
    for (uint8_t s = 0; s < SEATS; s++)   // seat order is already clockwise
        if ((h >> s) & 1)
            cand[n++] = s;
    uint8_t wi = rng_below(n);

    // Roulette: steps slow down (55 ms, x1.16 each) for 1.5 s, and the last step lands on the winner.
    uint16_t times[20];
    uint8_t k = 0;
    uint32_t gap = 5500;   // ms x 100
    for (uint16_t t = 0; t < 1500 && k < 20; gap = gap * 116 / 100) {
        times[k++] = t;
        t += gap / 100;
    }
    uint32_t t0 = millis();
    for (uint8_t i = 0; i < k; i++) {
        while (millis() - t0 < times[i])
            service();
        uint8_t idx = (uint8_t)(((int16_t)wi - (k - 1 - i)) % n + n) % n;
        for (uint8_t j = 0; j < n; j++)
            led[cand[j]] = j == idx ? gamma16(13) : gamma16(3);
        leds_show();
    }
    wait_ms(260);

    // Winner: flash bright/dim, fast for 2 s then slower; everything else off.
    uint8_t w = cand[wi];
    t0 = millis();
    for (;;) {
        service();
        uint32_t e = millis() - t0;
        if ((e >= SHOW_MIN_MS && !(held() & SEAT_BITS)) || e >= SHOW_MAX_MS)
            break;
        bool hi = e < 2000 ? (e / 125) % 2 == 0 : (e / 500) % 2 == 0;
        for (uint8_t s = 0; s < SEATS; s++)
            led[s] = 0;
        led[w] = hi ? gamma16(15) : gamma16(4);
        leds_show();
    }
    leds_clear();
    buttons_ignore_held();   // anyone still holding has to let go before the next round
    take_presses();
    return w;
}

Next picker_run() {
    uint8_t prev = 0;
    uint32_t since = millis();
    take_presses();
    for (;;) {
        service();
        uint16_t presses = take_presses();
        uint8_t h = held() & SEAT_BITS;
        if ((presses & MODE_BIT) && !h) {
            leds_clear();
            return TO_SIMON;
        }
        if (h != prev) {
            prev = h;
            since = millis();
        }
        uint8_t n = __builtin_popcount(h);
        uint32_t quiet = millis() - since;
        if (n >= 2 && quiet >= HOLD_MS) {
            pick_and_show(h);
            prev = 0;
            since = millis();
            continue;
        }
        if ((n == 0 && quiet >= SLEEP_EMPTY_MS) || (n == 1 && quiet >= SLEEP_ALONE_MS)) {
            leds_clear();
            return TO_SLEEP;
        }
        draw_waiting(h, n, since);
    }
}
