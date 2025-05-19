# jammer_detection_xapp.py

import time
import json
# Assume an OSC RIC SDK library for E2, RMR, SDL, logging etc.
# from ric_sdk import E2Client, RmrClient, SdlClient, Logger

# Configuration (could be loaded from a config map or via A1)
DETECTION_THRESHOLDS = {
    "sinr_drop_dB": 10,  # dB drop from moving average
    "bler_increase_abs": 0.3, # Absolute increase in BLER
    "consecutive_triggers_needed": 3
}
KPM_REPORT_INTERVAL_MS = 100 # How often to request KPM reports
MONITORED_CELL_ID = "Cell123" # Example

# Global state (in a real xApp, manage state more robustly, perhaps via SDL)
sinr_history = {} # {ue_id: [list of recent SINR values]}
bler_history = {} # {ue_id: [list of recent BLER values]}
jammer_detected_status = {} # {ue_id: {"count": 0, "last_detected_time": 0}}

class JammerDetectionXApp:
    def __init__(self):
        # self.logger = Logger(name="JammerDetectionXApp")
        # self.rmr_client = RmrClient() # For sending messages to other xApps
        # self.e2_client = E2Client(self.handle_e2_indication) # E2 termination and indication callback
        # self.sdl_client = SdlClient() # For shared data, e.g., cell info
        print("[INFO] JammerDetectionXApp initialized.")
        self.active_subscriptions = {} # Store subscription IDs

    def start(self):
        print("[INFO] JammerDetectionXApp starting...")
        # Example: Subscribe to KPMs for a specific cell or all cells
        # This is highly dependent on the E2SM KPM definition and RAN's E2 agent
        # The E2SM KPM subscription request would define:
        # - RAN Function ID (for KPM reporting)
        # - Event Trigger Definition (e.g., periodic reporting)
        # - Action Definition (report KPMs like SINR, RSRP, BLER)
        # - Reporting Interval
        
        # Placeholder for E2 Subscription logic
        # subscription_details = self.build_kpm_subscription_request(MONITORED_CELL_ID, KPM_REPORT_INTERVAL_MS)
        # sub_id = self.e2_client.subscribe(subscription_details)
        # if sub_id:
        #     self.active_subscriptions[sub_id] = subscription_details
        #     self.logger.info(f"Successfully subscribed to KPMs with sub_id: {sub_id}")
        # else:
        #     self.logger.error("Failed to subscribe to KPMs.")
        print(f"[INFO] Subscribed to KPMs for cell {MONITORED_CELL_ID} (simulated).")
        self.run_simulation_loop() # For demonstration without real E2

    def build_kpm_subscription_request(self, cell_id, interval_ms):
        # This function would construct the E2AP Subscription Request message
        # with the E2SM KPM payload, specifying desired KPIs (SINR, RSRP, BLER),
        # the cell/UE scope, and the reporting interval.
        # Returns a structured message for the E2 client.
        print(f"[DEBUG] Building KPM subscription for {cell_id}, interval {interval_ms}ms")
        # Actual implementation requires ASN.1 encoding for E2SM KPM
        return {"type": "E2SM_KPM_Subscription", "cell_id": cell_id, "interval": interval_ms, 
                "kpis": ["RSRP", "SINR", "DL_BLER"]}


    def handle_e2_indication(self, indication_message):
        # This callback is triggered when an E2 Indication (report) is received
        # print(f"[INFO] Received E2 Indication: {indication_message}")
        # header = indication_message.get_header()
        # payload = indication_message.get_payload() # This would be E2SM KPM data

        # Actual parsing of E2SM KPM (ASN.1 decoded) data needed here
        # For simplicity, assuming payload is a dict like:
        # {'ue_reports': [{'ue_id': 'UE1', 'sinr': 15, 'bler': 0.05}, ...]}
        
        # --- SIMULATED INDICATION FOR DEMO ---
        import random
        payload = {"ue_reports": []}
        if random.random() < 0.3: # Simulate a jamming event for UE1
             payload["ue_reports"].append({"ue_id": "UE1", "sinr": random.uniform(-5, 5), "bler": random.uniform(0.4, 0.8)})
        else:
             payload["ue_reports"].append({"ue_id": "UE1", "sinr": random.uniform(10, 25), "bler": random.uniform(0, 0.1)})
        payload["ue_reports"].append({"ue_id": "UE2", "sinr": random.uniform(10, 25), "bler": random.uniform(0, 0.1)})
        # --- END SIMULATED INDICATION ---

        if "ue_reports" in payload:
            for report in payload["ue_reports"]:
                ue_id = report.get("ue_id")
                current_sinr = report.get("sinr")
                current_bler = report.get("bler")

                if ue_id and current_sinr is not None and current_bler is not None:
                    self.process_ue_kpis(ue_id, current_sinr, current_bler)

    def process_ue_kpis(self, ue_id, sinr, bler):
        print(f"[DATA] UE_ID: {ue_id}, SINR: {sinr:.2f} dB, DL_BLER: {bler:.2f}")

        # Update history (implement moving average or more sophisticated tracking)
        if ue_id not in sinr_history:
            sinr_history[ue_id] = []
            bler_history[ue_id] = []
            jammer_detected_status[ue_id] = {"count": 0, "last_detected_time": 0}

        sinr_history[ue_id].append(sinr)
        bler_history[ue_id].append(bler)
        if len(sinr_history[ue_id]) > 10: # Keep last 10 samples for avg
            sinr_history[ue_id].pop(0)
            bler_history[ue_id].pop(0)

        # Basic Detection Logic (Example - needs significant refinement)
        jam_event_detected = False
        if len(sinr_history[ue_id]) >= 5: # Need enough history
            avg_sinr = sum(sinr_history[ue_id][:-1]) / len(sinr_history[ue_id][:-1]) if len(sinr_history[ue_id][:-1]) > 0 else sinr
            
            if (avg_sinr - sinr) > DETECTION_THRESHOLDS["sinr_drop_dB"]:
                print(f"[ALERT] UE_ID: {ue_id} - Significant SINR drop detected! Current: {sinr:.2f}, Avg: {avg_sinr:.2f}")
                jam_event_detected = True
            
            if bler > DETECTION_THRESHOLDS["bler_increase_abs"] and sinr < (avg_sinr - DETECTION_THRESHOLDS["sinr_drop_dB"]/2) : # BLER high and SINR somewhat low
                 print(f"[ALERT] UE_ID: {ue_id} - High BLER detected! BLER: {bler:.2f}, SINR: {sinr:.2f}")
                 jam_event_detected = True
        
        # Debouncing / Consecutive trigger logic
        if jam_event_detected:
            jammer_detected_status[ue_id]["count"] += 1
        else:
            jammer_detected_status[ue_id]["count"] = 0 # Reset if condition not met

        if jammer_detected_status[ue_id]["count"] >= DETECTION_THRESHOLDS["consecutive_triggers_needed"]:
            # Avoid flooding with messages if already detected recently
            if time.time() - jammer_detected_status[ue_id]["last_detected_time"] > 10: # Cooldown period (10s)
                self.publish_jamming_detected_event(ue_id, {"sinr": sinr, "bler": bler, "reason": "Thresholds breached"})
                jammer_detected_status[ue_id]["last_detected_time"] = time.time()
                jammer_detected_status[ue_id]["count"] = 0 # Reset after publishing


    def publish_jamming_detected_event(self, ue_id, details):
        event_message = {
            "event_type": "JAMMING_DETECTED",
            "ue_id": ue_id,
            "timestamp": time.time(),
            "details": details
        }
        # self.rmr_client.send_message(message_type="JAM_DETECT_MSG", payload=json.dumps(event_message))
        print(f"[EVENT] Published JAMMING_DETECTED for UE_ID: {ue_id}, Details: {details}")

    def run_simulation_loop(self): # For demo purposes without real E2
        print("[INFO] Starting simulated KPM reporting loop...")
        try:
            while True:
                # Simulate receiving an E2 indication
                self.handle_e2_indication(None) # Pass None as we simulate payload inside
                time.sleep(KPM_REPORT_INTERVAL_MS / 1000.0) # Simulate report interval
        except KeyboardInterrupt:
            print("[INFO] Simulation loop stopped.")
            self.stop()

    def stop(self):
        print("[INFO] JammerDetectionXApp stopping...")
        # for sub_id in self.active_subscriptions:
        #     self.e2_client.unsubscribe(sub_id)
        # self.rmr_client.close()
        # self.e2_client.close()
        # self.sdl_client.close()
        print("[INFO] JammerDetectionXApp stopped.")

if __name__ == "__main__":
    detection_xapp = JammerDetectionXApp()
    detection_xapp.start()
    # In a real RIC, the xApp manager would handle start/stop