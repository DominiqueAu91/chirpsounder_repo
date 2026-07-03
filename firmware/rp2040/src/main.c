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

/* V0.4: Core 1 → Core 0 completion handshake. Core 1 is the single
 * writer of these flags; Core 0 is the single reader and clears them
 * on state entry. Single-producer/single-consumer bool flags are safe
 * on RP2040 without further synchronization. */
static volatile bool cw_id_done = false;
static volatile bool dwell_done = false;

/* V0.4: seconds of TX since the last CW identification; regulatory.md
 * requires re-identification at least every 10 minutes. */
static uint32_t tx_seconds_since_id = 0;
#define REID_INTERVAL_S 600

/* Core 1 entry: RF chain control loop */
void core1_main(void) {
    while (true) {
        if (current_state == STATE_DWELL_TX) {
            rf_chain_emit_chirp_dwell();   /* blocks for one dwell */
            dwell_done = true;
        } else if (current_state == STATE_CW_ID || current_state == STATE_CW_ID_FINAL) {
            rf_chain_emit_cw_callsign();   /* blocks until callsign sent */
            cw_id_done = true;
        } else {
            rf_chain_idle();
        }
        sleep_ms(10);
    }
}

/* State machine on Core 0 */
state_t state_machine_step(state_t s) {
    if (safety_pa_fault_active() && s != STATE_FAULT) {
        safety_set_pa_enable(false);   /* V0.4: belt-and-braces — drop GP15
                                          even though the hardware chain has
                                          already opened the relay */
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
            cw_id_done = false;
            return STATE_CW_ID;

        case STATE_CW_ID:
            /* V0.4 FIX: wait for Core 1 to finish the callsign. The V0.2
             * skeleton transitioned after one 50 ms tick — the CW ID never
             * completed on air. */
            if (cw_id_done) {
                tx_seconds_since_id = 0;
                dwell_done = false;
                return STATE_DWELL_TX;
            }
            return STATE_CW_ID;

        case STATE_DWELL_TX:
            if (dwell_done) {
                tx_seconds_since_id += config_dwell_seconds();
                return STATE_PAUSE;
            }
            return STATE_DWELL_TX;

        case STATE_PAUSE:
            if (logging_schedule_complete()) {
                cw_id_done = false;
                return STATE_CW_ID_FINAL;
            }
            /* V0.4 FIX: regulatory re-identification every 10 minutes of
             * accumulated TX time. V0.2 looped PAUSE → DWELL_TX and only
             * identified at start and end of schedule. */
            if (tx_seconds_since_id >= REID_INTERVAL_S) {
                cw_id_done = false;
                return STATE_CW_ID;
            }
            dwell_done = false;
            return STATE_DWELL_TX;

        case STATE_CW_ID_FINAL:
            if (cw_id_done) return STATE_IDLE;
            return STATE_CW_ID_FINAL;

        case STATE_FAULT:
            /* V0.4 FIX: the V0.2 skeleton gated on a fault_acknowledged
             * flag that no code path ever set — FAULT was unrecoverable.
             * Policy (docs/cards/06-safety.md): MENU acknowledges after
             * the operator has physically verified the cause. */
            if (ihm_button_pressed(BTN_MENU)) {
                logging_record_fault_ack();
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
