# Class 700 / Desiro City - Traction & Auxiliary Power Fault Troubleshooting Manual
**Document ID:** TS-700-TRAC-MAN-004  
**Revision:** 3.2  
**Applicable Fleets:** Thameslink Class 700/0, Class 700/1  
**Author:** Rolling Stock Technical Services  

---

## 1. General Safety & Isolation Requirements
Before attempting any inspection or remedial action within the High Voltage (HV) equipment enclosures or Traction Inverter cubicles:
- Verify that the pantograph is lowered and isolated from the 25 kV AC overhead line, or third rail shoegear is isolated from 750 V DC.
- Apply the master safety padlock and verify zero voltage using an approved indicator.
- Ensure the train auxiliary batteries are switched OFF if instructed by the specific fault code procedure.

---

## 2. Traction Fault Codes Index & Diagnostic Procedures

### Fault Code: FC 4103 - Traction Motor Inverter Over-Temperature
- **Severity:** High (Red alert on Driver Machine Interface / TCMS)
- **Subsystem:** Traction & Auxiliaries
- **Page Reference:** Page 42

#### Description
Fault Code 4103 triggers when the IGBT temperature sensor on Traction Inverter Unit 1 or Unit 2 registers a junction temperature exceeding 115°C for longer than 3.5 seconds, or when cooling coolant flow falls below 18 L/min.

#### Immediate Operational Consequence
- TCMS derates traction power to 50% on the affected motor bogie.
- If temperature continues to rise above 125°C, the affected traction line contactor (TLC) opens automatically.

#### Remedial Troubleshooting Procedure
1. Check TCMS diagnostic screen to identify whether Inverter Unit 1 (Coach 2) or Unit 2 (Coach 7) reported the alert.
2. Verify that the Traction Converter Cooling Fan Circuit Breaker `=24-F01` located in Aux Panel 3 is in the CLOSED position. If tripped, reset once only.
3. Inspect coolant reservoir level gauge on the underframe cooling module. Ensure level is between MIN and MAX marks.
4. Check for debris blocking the external radiator cooling matrix under Coach 2/7.
5. If coolant level is normal and fan is operating, allow a 10-minute cooldown period and perform a TCMS fault reset via soft-key 4 on the cab display.
6. If FC 4103 re-latches immediately, isolate the affected inverter via switch `=24-S02` to allow single-inverter degraded transit to depot.

---

### Fault Code: FC 2814 - DC Bus Overvoltage Spike
- **Severity:** Medium
- **Subsystem:** Traction
- **Page Reference:** Page 58

#### Description
Detected during regenerative braking transitions on 750 V DC third-rail sections when the substation cannot absorb regenerated current and the dynamic brake resistor contactor fails to pick up within 50 ms.

#### Remedial Troubleshooting Procedure
1. Inspect dynamic braking resistor fuse `=22-F14`.
2. Inspect brake chopper gate drive board LED status:
   - Green: Normal standby
   - Amber blinking: Chopper thermal limit approaching
   - Red steady: Chopper IGBT failure - isolate Motor Car 1.

---

## 3. Passenger Door Subsystem Fault Codes

### Fault Code: FC 1205 - Exterior Door Interlock Loop Open in Motion
- **Severity:** Critical Safety Failure
- **Subsystem:** Doors
- **Page Reference:** Page 84

#### Description
The Door Closed and Locked (DC&L) electrical loop interrupted while vehicle speed signal > 3 km/h. Traction interlock immediately inhibits traction demand and commands emergency brake application (EB).

#### Remedial Troubleshooting Procedure
1. Observe Cab Door Status Panel to isolate the affected vehicle and door leaf (Door 1 to Door 8).
2. Dispatch technician to local door leaf:
   - Check if obstacle is physically lodged in the lower door guide track.
   - Inspect microswitch `=41-S08` (Door Closed Proving switch) for mechanical deflection or sticking.
3. If mechanically unobstructed, verify 24 V DC supply across test pin `TP-04` on the Electronic Door Control Unit (EDCU).
4. If EDCU shows internal failure, use manual square key to mechanically lock and isolate door leaf. Apply yellow "Out of Order" door barrier.
5. Turn Door Isolation Switch `=41-S10` to BYPASS to re-establish the traction safety loop and allow train movement under depot supervision.
