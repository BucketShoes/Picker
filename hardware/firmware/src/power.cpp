#include <avr/interrupt.h>
#include <avr/sleep.h>
#include <avr/wdt.h>
#include <util/delay.h>
#include "board.h"
#include "buttons.h"
#include "leds.h"
#include "power.h"

static volatile uint8_t woke_by_pin;

ISR(PCINT0_vect) { woke_by_pin = 1; }
ISR(PCINT1_vect, ISR_ALIASOF(PCINT0_vect));
ISR(PCINT2_vect, ISR_ALIASOF(PCINT0_vect));
EMPTY_INTERRUPT(WDT_vect);

static void watchdog(uint8_t on) {   // interrupt only (no reset), 8 s
    cli();
    wdt_reset();
    MCUSR &= ~_BV(WDRF);
    WDTCSR = _BV(WDCE) | _BV(WDE);
    WDTCSR = on ? (_BV(WDIE) | _BV(WDP3) | _BV(WDP0)) : 0;
    sei();
}

void power_sleep() {
    leds_clear();
    leds_stop();
    _delay_us(20);
    uint16_t stuck = btn_raw();
    for (;;) {
        uint8_t sb, sc, sd;
        btn_port_masks(stuck, &sb, &sc, &sd);
        PORTB &= ~sb; DDRB |= sb;            // stuck: output low, no pull-up current
        PORTC &= ~sc; DDRC |= sc;
        PORTD &= ~sd; DDRD |= sd;
        PCMSK0 = BTN_PB & ~sb;               // and no wake from it
        PCMSK1 = BTN_PC & ~sc;
        PCMSK2 = BTN_PD & ~sd;
        woke_by_pin = 0;
        PCIFR = _BV(PCIF0) | _BV(PCIF1) | _BV(PCIF2);
        PCICR = _BV(PCIE0) | _BV(PCIE1) | _BV(PCIE2);
        watchdog(stuck != 0);

        set_sleep_mode(SLEEP_MODE_PWR_DOWN);
        cli();
        if (!woke_by_pin) {                  // a press between enabling the wake and here must not be lost
            sleep_enable();
#ifdef sleep_bod_disable
            sleep_bod_disable();
#endif
            sei();
            sleep_cpu();
            sleep_disable();
        }
        sei();

        PCICR = 0;
        watchdog(0);
        DDRB &= ~sb; PORTB |= sb;            // back to pull-up inputs
        DDRC &= ~sc; PORTC |= sc;
        DDRD &= ~sd; PORTD |= sd;
        if (woke_by_pin)
            break;
        _delay_us(20);                       // watchdog: let the pull-ups settle, then see which are released
        stuck &= btn_raw();
    }
    buttons_reset(stuck);                    // still-stuck buttons stay ignored until released
    leds_start();
}
