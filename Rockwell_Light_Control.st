/*
================================================================================
                    ROCKWELL PLC STRUCTURED TEXT - LIGHT CONTROL
                         Direct Copy/Paste Ready Program
================================================================================

PURPOSE:
    Light bulb control using Structured Text for Allen-Bradley ControlLogix.
    Single pushbutton toggles light on/off with startup default as OFF.

HARDWARE:
    - Input Toggle_Switch → I:1/0 (NO pushbutton for toggle)
    - Output Light_Bulb   → O:2/0 (Light output)

CONTROLLER: Allen-Bradley ControlLogix/CompactLogix
SOFTWARE: Studio 5000 Structured Text Routine

AUTHORS: Greg Skovira
DATE: November 15, 2025
================================================================================
*/

PROGRAM Light_Control_Toggle

VAR
    Toggle_Switch  : BOOL := I:1/0;     /* Toggle pushbutton input */
    Light_Bulb     : BOOL := O:2/0;     /* Light output */
    Light_Status   : BOOL := FALSE;     /* Light state (default OFF) */
    Toggle_OneShot : BOOL := FALSE;     /* One-shot for toggle button */
    Toggle_Prev    : BOOL := FALSE;     /* Previous toggle state */
END_VAR

/* ======================================================================= */
/* SINGLE BUTTON TOGGLE LOGIC - DEFAULT OFF ON STARTUP                   */
/* ======================================================================= */

/* Detect rising edge of toggle switch (button press) */
Toggle_OneShot := Toggle_Switch AND NOT Toggle_Prev;
Toggle_Prev := Toggle_Switch;

/* Toggle light state on each button press */
IF Toggle_OneShot THEN
    Light_Status := NOT Light_Status;   /* Flip the state */
END_IF;

/* Output to physical light */
Light_Bulb := Light_Status;
O:2/0 := Light_Bulb;

END_PROGRAM

/*
================================================================================
                              ALTERNATIVE METHOD
================================================================================
*/

PROGRAM Light_Control_Alt

VAR
    /* Direct I/O mapping */
    ON_Btn        AT %I1.0 : BOOL;     /* Input I:1/0 */
    OFF_Btn       AT %I1.1 : BOOL;     /* Input I:1/1 */
    Light_Out     AT %Q2.0 : BOOL;     /* Output O:2/0 */
    
    /* Control variables */
    Light_Cmd     : BOOL := FALSE;
    Start_Edge    : R_TRIG;            /* Rising edge trigger */
    Stop_Edge     : R_TRIG;            /* Rising edge trigger */
END_VAR

/* One-shot detection for button presses */
Start_Edge(CLK := ON_Btn);
Stop_Edge(CLK := OFF_Btn);

/* Light control logic with priority for OFF */
IF Stop_Edge.Q THEN
    Light_Cmd := FALSE;                 /* OFF has priority */
ELSIF Start_Edge.Q THEN
    Light_Cmd := TRUE;                  /* Turn light ON */
END_IF;

/* Safety: OFF button always overrides */
IF OFF_Btn THEN
    Light_Cmd := FALSE;
END_IF;

/* Output assignment */
Light_Out := Light_Cmd;

END_PROGRAM

/*
================================================================================
                           SIMPLE ONE-LINE VERSION
================================================================================
*/

PROGRAM Light_Control_Simple

VAR
    Light_Latch : BOOL := FALSE;
END_VAR

/* Single line solution with SR latch behavior */
Light_Latch := (Light_Latch OR I:1/0) AND NOT I:1/1;
O:2/0 := Light_Latch;

END_PROGRAM