/*
 * main.c — Chirpsounder TX RP2040 firmware skeleton
 *
 * Dual-core architecture:
 *   Core 0: state machine, IHM, USB host logging
 *   Core 1: RF chain control, PPS-aligned sequencing
 *
 * State machine: BOOT → IDLE → ARMING → CW_ID → DWELL_TX → PAUSE → ... → CW_ID_FINAL
 *                Any state → FAULT on PA_FAULT signal
 *
 * Author: Dominique Auprince
 * License: GPL-3.0-or-later
 */

#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "hardware/i2c.h"
#include "hardware/spi.h"
#include "hardware/adc.h"

#include "config.h"
#include "coherence.h"
#include "rf_low.h"
#include "rf_high.h"
#include "ihm.h"
#include "safety.h"
#include "logging.h"

typedef enum {
    STATE_BOOT,
    STATE_IDLE,
    STATE_ARMING,
    STATE_CW_ID,
    STATE_DWELL_TX,
    STATE_PAUSE,
    STATE_CW_ID_FINAL,
    STATE_FAULT,
} state_t;

static volatile state_t current_state = STATE_BOOT;
static volatile bool fault_acknowledged = false;

/* Core 1 entry: RF chain control loop */
void core1_main(void) {
    while (true) {
        if (current_state == STATE_DWELL_TX) {
            rf_chain_emit_chirp_dwell();
        } else if (current_state == STATE_CW_ID || current_state == STATE_CW_ID_FINAL) {
            rf_chain_emit_cw_callsign();
        } else {
            rf_chain_idle();
        }
        sleep_ms(10);
    }
}

/* State machine on Core 0 */
state_t state_machine_step(state_t s) {
    if (safety_pa_fault_active()) {
        logging_record_fault();
        return STATE_FAULT;
    }
    switch (s) {
        case STATE_BOOT:
            ihm_init();
            coherence_init();
            rf_low_init();
            rf_high_init();
            safety_init();
            logging_init();
            return STATE_IDLE;

        case STATE_IDLE:
            if (ihm_button_pressed(BTN_RUN)) return STATE_ARMING;
            return STATE_IDLE;

        case STATE_ARMING:
            if (!coherence_gpsdo_locked()) {
                ihm_show_error("GPSDO not locked");
                return STATE_IDLE;
            }
            if (!safety_self_test()) {
                ihm_show_error("Safety self-test failed");
                return STATE_FAULT;
            }
            return STATE_CW_ID;

        case STATE_CW_ID:
            return STATE_DWELL_TX;

        case STATE_DWELL_TX:
            if (logging_dwell_complete()) return STATE_PAUSE;
            return STATE_DWELL_TX;

        case STATE_PAUSE:
            if (logging_schedule_complete()) return STATE_CW_ID_FINAL;
            return STATE_DWELL_TX;

        case STATE_CW_ID_FINAL:
            return STATE_IDLE;

        case STATE_FAULT:
            if (ihm_button_pressed(BTN_MENU) && fault_acknowledged) {
                fault_acknowledged = false;
                return STATE_IDLE;
            }
            return STATE_FAULT;
    }
    return STATE_IDLE;
}

int main(void) {
    stdio_init_all();
    multicore_launch_core1(core1_main);

    while (true) {
        current_state = state_machine_step(current_state);
        ihm_refresh_display(current_state);
        safety_kick_watchdog();
        sleep_ms(50);
    }
    return 0;
}
