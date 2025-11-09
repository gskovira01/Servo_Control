#include "ClearCore.h"
#include <Ethernet.h>

//***********************************************************************
//*******************Declare variables******************************
#define BOARD_ID 1 // Change to 2 for the second board
//*******************Ethernet Variables******************************
// At the top, before setup()
byte mac1[] = {0x24, 0x15, 0x10, 0xb0, 0x42, 0x3e};
byte mac2[] = {0x24, 0x15, 0x10, 0xb0, 0x43, 0xe9};
IPAddress ip1(192, 168, 1, 171);
IPAddress ip2(192, 168, 1, 172);
unsigned int localPort1 = 8888;
unsigned int localPort2 = 8890;
#define MAX_PACKET_LENGTH 100
// Buffer for holding received packets.
char packetReceived[MAX_PACKET_LENGTH];

// The remote ClearCore's IP address and port
IPAddress remoteIp(192, 168, 1, 100);
unsigned int remotePort = 8889;

// The last time you sent a packet to the remote device, in milliseconds.
unsigned long lastSendTime = 0;
// Delay between sending packets, in milliseconds
const unsigned long sendingInterval = 2*1000;

// An EthernetUDP instance to let us send and receive packets over UDP
EthernetUDP Udp;

// Set this false if not using DHCP to configure the local IP address.
bool usingDhcp = false;

unsigned long lastLoopTime = 0;
const unsigned long loopInterval = 2000; // 2 seconds in milliseconds


// This example has built-in functionality to automatically clear motor alerts,
// including motor shutdowns. Any uncleared alert will cancel and disallow motion.
#define HANDLE_ALERTS (0)

int LoopCount = 0;
unsigned long currentMillis;
unsigned long previousMillis = 0;  // Stores the last time the event was triggered
const long interval = 1000;        // Interval at which to trigger the event (milliseconds)

// Declare user-defined helper functions
enum MoveState {
    MOVE_IDLE,
    MOVE_CHECK_ALERTS,
    MOVE_START,
    MOVE_WAIT_HLFB,
    MOVE_DONE
};

bool MoveAbsolutePosition(MotorDriver &motor, int position, MoveState &moveState, unsigned long &moveStartTime, unsigned long &lastMillis, int &lastPosition);
//void PrintAlerts();
//void HandleMotorAlerts(MotorDriver &motor, const char *motorName);
//void HandleAlerts();

// Define input pins 1, 2, 3, and 4 used to enable/disable motors
#define inputPin1 IO0
#define inputPin2 IO1
#define inputPin3 IO2
#define inputPin4 IO3

int next_step_last = 0;
int next_step = 0;
String inputString = "";  // A string to hold incoming data

// Define variables for motor enable
bool motor1_enable;
bool motor2_enable;
bool motor3_enable;
bool motor4_enable;
        
bool motor1Done;
bool motor2Done;
bool motor3Done;
bool motor4Done;

// Define the motors
MotorDriver &motor1 = ConnectorM0;
MotorDriver &motor2 = ConnectorM1;
MotorDriver &motor3 = ConnectorM2;
MotorDriver &motor4 = ConnectorM3;

//bool motor1MoveDistance(MotorDriver &motor,int distance);
//bool motor2MoveDistance(MotorDriver &motor,int distance);
//bool motor3MoveDistance(MotorDriver &motor,int distance);
//bool motor4MoveDistance(MotorDriver &motor,int distance);

// Define limits for velocity and acceleration
int velocityLimit1 = 1000; // pulses per sec
int accelerationLimit1 = 100000; // pulses per sec^2

int velocityLimit2 = 1000; // pulses per sec
int accelerationLimit2 = 100000; // pulses per sec^2

int velocityLimit3 = 1000; // pulses per sec
int accelerationLimit3 = 100000; // pulses per sec^2

int velocityLimit4 = 1000; // pulses per sec
int accelerationLimit4 = 100000; // pulses per sec^2

// Variables to store parsed data
// Buttons
bool Mode = 0;  //1 = Auto 0 = Manual
bool Start = 0;  //1 = Auto 0 = Manual
bool Repeat = 0;  //1 = Auto 0 = Manual
bool S1B1 = 1;  // Servo1 Button 1
bool S1B2 = 0;  // Servo1 Button 2
bool S2B1 = 1;  // Servo2 Button 1
bool S2B2 = 0;  // Servo2 Button 2
bool S3B1 = 1;  // Servo3 Button 1
bool S3B2 = 0;  // Servo3 Button 2
bool S4B1 = 1;  // Servo4 Button 1
bool S4B2 = 0;  // Servo4 Button 2
//Values
int S1V = 0;  // Servo1 Velocity
int S1A = 0;  // Servo1 Actual
int S1P = 0;  // Servo1 Position
int S2V = 0;  // Servo2 Velocity
int S2A = 0;  // Servo2 Actual
int S2P = 0;  // Servo2 Position
int S3V = 0;  // Servo3 Velocity
int S3A = 0;  // Servo3 Actual
int S3P = 0;  // Servo3 Position
int S4V = 0;  // Servo4 Velocity
int S4A = 0;  // Servo4 Actual
int S4P = 0;  // Servo4 Position
// Setpoints
int S1V_SPT = 250;  // Servo1 Velocity
int S1A_SPT = 2000;  // Servo1 Acceleration
int S1P_SPT = 0;  // Servo1 Position
int S2V_SPT = 250;  // Servo2 Velocity
int S2A_SPT = 2000;  // Servo2 Position
int S2P_SPT = 0;  // Servo2 Position
int S3V_SPT = 250;  // Servo3 Velocity
int S3A_SPT = 2000;  // Servo3 Actual
int S3P_SPT = 0;  // Servo3 Position
int S4V_SPT = 500;  // Servo4 Velocity
int S4A_SPT = 250;  // Servo4 Actual
int S4P_SPT = 0;  // Servo4 Position

// Add these global variables for previous velocity and time
// Add these global variables at the top of your file:
int prev_S1V = 0, prev_S2V = 0, prev_S3V = 0, prev_S4V = 0;
unsigned long prev_S1V_time = 0, prev_S2V_time = 0, prev_S3V_time = 0, prev_S4V_time = 0;

//Gains Constants
float KV1 = 100;  // Postion Gain
float KA1 = 1;  // Postion Gain 
float KP1 = 1;  // Postion Gain 

float KV2 = 100;  // Postion Gain
float KA2 = 1;  // Postion Gain 
float KP2 = 1;  // Postion Gain  

float KV3 = 1;  // Postion Gain
float KA3 = 1;  // Postion Gain 
float KP3 = 1;  // Postion Gain  

float KV4 = 1;  // Postion Gain
float KA4 = 1;  // Postion Gain 
float KP4 = 1;  // Postion Gain 

int PrimaryAddress = 2000;
int SecondaryAddress = 2000;
int PrimaryTOS = 0;
int SecondaryTOS = 0;
int PrimaryFinish = 4000;
int SecondaryFinish = 4000;


// Primary Rotation : motor 1 - Define a 11 by 3 array for velocity setpoints, acceleration, and position
int motor1_setpoints[11][3] = {
    {10, 8000, 2000}, // Idle              :  Step 0 : Velocity 0, Acceleration 0, Position 0
    {10, 8000, 2000}, // Address           :  Step 1 : Velocity 1, Acceleration 1, Position 1
    {10, 8000, 1500}, // Initial Take Away :  Step 2 : Velocity 1, Acceleration 1, Position 1
    {10, 8000, 1000}, // Take Away         :  Step 3 : Velocity 1, Acceleration 1, Position 1
    {10, 8000, 500}, // Full Rotation      :  Step 4 : Velocity 1, Acceleration 1, Position 1
    {10, 8000, 0}, // Top of Swing      :  Step 5 : Velocity 1, Acceleration 1, Position 1
    {100, 8000, 500}, // Initial Downswing :  Step 6 : Velocity 1, Acceleration 1, Position 1
    {100, 8000, 1000}, // Release           :  Step 7 : Velocity 1, Acceleration 1, Position 1
    {100, 8000, 2000}, // Impact            :  Step 8 : Velocity 1, Acceleration 1, Position 1
    {100, 8000, 2500}, // Follow Through    :  Step 9 : Velocity 1, Acceleration 1, Position 1
    {100, 8000, 4000}, // Finish            :  Step 10 : Velocity 1, Acceleration 1, Position   
};

// Secondary Rotation : motor 2 - Define a 11 by 3 array for velocity setpoints, acceleration, and position
int motor2_setpoints[11][3] = {
    {12, 8000, 2000},  // Idle              :  Step 0 : Velocity 0, Acceleration 0, Position 0
    {12, 8000, 2000}, // Address           :  Step 1 : Velocity, Acceleration, Position
    {12, 8000, 2000}, // Initial Take Away :  Step 2 : Velocity, Acceleration, Position
    {12, 8000, 2000}, // Take Away         :  Step 3 : Velocity, Acceleration, Position
    {12, 8000, 0}, // Full Rotation     :  Step 4 : Velocity, Acceleration, Position
    {12, 8000, 0}, // Top of Swing      :  Step 5 : Velocity, Acceleration, Position
    {102, 8000, 0}, // Initial Downswing :  Step 6 : Velocity, Acceleration, Position
    {102, 8000, 500}, // Release           :  Step 7 : Velocity, Acceleration, Position
    {102, 8000, 2000}, // Impact            :  Step 8 : Velocity, Acceleration, Position
    {102, 8000, 3000}, // Follow Through    :  Step 9 : Velocity, Acceleration, Position
    {102, 8000, 4000}, // Finish            :  Step 10 : Velocity, Acceleration, Position
};

// Tertiary Lift : motor 3 - Define a 11 by 3 array for velocity setpoints, acceleration, and position
int motor3_setpoints[11][3] = {
    {1003, 8000, 000}, // Idle              :  Step 0 : Velocity, Acceleration, Position
    {2003, 8000, 900}, // Address           :  Step 1 : Velocity, Acceleration, Position
    {2003, 8000, 800}, // Initial Take Away :  Step 2 : Velocity, Acceleration, Position
    {2003, 8000, 700}, // Take Away         :  Step 3 : Velocity, Acceleration, Position
    {2003, 8000, 600}, // Full Rotation     :  Step 4 : Velocity, Acceleration, Position
    {2003, 8000, 500}, // Top of Swing      :  Step 5 : Velocity, Acceleration, Position
    {2003, 8000, 600}, // Initial Downswing :  Step 6 : Velocity, Acceleration, Position
    {2003, 8000, 700}, // Release           :  Step 7 : Velocity, Acceleration, Position
    {2003, 8000, 800}, // Impact            :  Step 8 : Velocity, Acceleration, Position 
    {2003, 8000, 900}, // Follow Through    :  Step 9 : Velocity, Acceleration, Position
    {2003, 8000, 1000}, // Finish            :  Step 10 : Velocity, Acceleration, Position
};

// Tertiary Rotation : motor 4 - Define a 11 by 3 array for velocity setpoints, acceleration, and position
int motor4_setpoints[11][3] = {
    {500, 2000, 000}, // Idle              :  Step 0 : Velocity, Acceleration, Position
    {500, 5000, 400}, // Address           :  Step 1 : Velocity, Acceleration, Position
    {500, 5000, 400}, // Initial Take Away :  Step 2 : Velocity, Acceleration, Position
    {500, 5000, 270}, // Take Away         :  Step 3 : Velocity, Acceleration, Position
    {500, 5000, 125}, // Full Rotation     :  Step 4 : Velocity, Acceleration, Position
    {500, 5000, 000}, // Top of Swing      :  Step 5 : Velocity, Acceleration, Position
    {500, 5000, 300}, // Initial Downswing :  Step 6 : Velocity, Acceleration, Position
    {500, 5000, 356}, // Release           :  Step 7 : Velocity, Acceleration, Position
    {500, 5000, 390}, // Impact            :  Step 8 : Velocity, Acceleration, Position
    {500, 5000, 415}, // Follow Through    :  Step 9 : Velocity, Acceleration, Position
    {500, 5000, 623}, // Finish   
};

MoveState moveState1 = MOVE_IDLE;
MoveState moveState2 = MOVE_IDLE;
MoveState moveState3 = MOVE_IDLE;
MoveState moveState4 = MOVE_IDLE;

unsigned long moveStartTime1;
unsigned long moveStartTime2;
unsigned long moveStartTime3;
unsigned long moveStartTime4;

const unsigned long moveTimeout = 10000; // Timeout in milliseconds

// Add these variables at the top with other global declarations
unsigned long lastMillis1 = 0, lastMillis2 = 0, lastMillis3 = 0, lastMillis4 = 0;
int lastPosition1 = 0, lastPosition2 = 0, lastPosition3 = 0, lastPosition4 = 0;

// Add these global variables near the top with other declarations
int initialPosition1 = 0, initialPosition2 = 0, initialPosition3 = 0, initialPosition4 = 0;

// Define the interval for calculating position and speed (in milliseconds)
const unsigned long calculationInterval = 100; // 100ms interval

// Add these variables at the top with other global declarations
unsigned long lastCalculationTime = 0;

// Add these variables at the top with other global declarations
unsigned long lastStateEngineStepTime = 0;
const unsigned long stateEngineStepInterval = 3000; // 1 second interval

// Add these variables at the top with other global declarations
unsigned long lastReportDataTime = 0;
const unsigned long ReportDataInterval = 3000; // 3 second interval

//***********************************************************************

void parseData(String data, int &V, int &A, int &P);
void handleCommand(String command);
void sendCurrentValues();
void sendButtonStates();
void sendSetpoints();
void CalculateAcceleration(MotorDriver &motor, int &acceleration, unsigned long &lastMillis, int &lastVelocity);
void sendStateEngineStep();
void loadMotorSetpoints();
void loadSetpoints(int step);

//***********************************************************************
void setup() {

Serial.begin(9600); 

byte* mac;
IPAddress ip;
unsigned int localPort;
if (BOARD_ID == 1) {
    mac = mac1;
    ip = ip1;
    localPort = localPort1;
} else {
    mac = mac2;
    ip = ip2;
    localPort = localPort2;
}
Ethernet.begin(mac, ip);
Udp.begin(localPort);

    // Make sure the physical link is up before continuing.
    while (Ethernet.linkStatus() == LinkOFF) {
        Serial.println("The Ethernet cable is unplugged...");
        delay(1000);
    }
    // Begin listening on the local port for UDP datagrams
    Udp.begin(localPort);
    Serial.println("UDP listener started.");
    
    uint32_t timeout = 2000;
    uint32_t startTime = millis();
    while (!Serial && millis() - startTime < timeout) {
        continue;
    }

    next_step = 0;
    // Read input pins to see if hardware enable is set for the four motors
    motor1_enable = digitalRead(inputPin1);
    motor2_enable = digitalRead(inputPin2);
    motor3_enable = digitalRead(inputPin3);
    motor4_enable = digitalRead(inputPin4);

    // Motor Setup
    MotorMgr.MotorInputClocking(MotorManager::CLOCK_RATE_NORMAL);
    MotorMgr.MotorModeSet(MotorManager::MOTOR_ALL, Connector::CPM_MODE_STEP_AND_DIR);

    // Motor1 Settings
    motor1.HlfbMode(MotorDriver::HLFB_MODE_HAS_BIPOLAR_PWM);
    motor1.HlfbCarrier(MotorDriver::HLFB_CARRIER_482_HZ);
    motor1.VelMax(velocityLimit1);
    motor1.AccelMax(accelerationLimit1);

    // Motor2 Settings
    motor2.HlfbMode(MotorDriver::HLFB_MODE_HAS_BIPOLAR_PWM);
    motor2.HlfbCarrier(MotorDriver::HLFB_CARRIER_482_HZ);
    motor2.VelMax(velocityLimit2);
    motor2.AccelMax(accelerationLimit2);

    // Motor3 Settings
    motor3.HlfbMode(MotorDriver::HLFB_MODE_HAS_BIPOLAR_PWM);
    motor3.HlfbCarrier(MotorDriver::HLFB_CARRIER_482_HZ);
    motor3.VelMax(velocityLimit3);
    motor3.AccelMax(accelerationLimit3);

    // Motor4 Settings
    motor4.HlfbMode(MotorDriver::HLFB_MODE_HAS_BIPOLAR_PWM);
    motor4.HlfbCarrier(MotorDriver::HLFB_CARRIER_482_HZ);
    motor4.VelMax(velocityLimit4);
    motor4.AccelMax(accelerationLimit4);

    // Remove the invalid debug prints that were here
    
    motor1.EnableRequest(motor1_enable);
    Serial.println("Motor1 Enabled");
    motor2.EnableRequest(motor2_enable);
    Serial.println("Motor2 Enabled");
    motor3.EnableRequest(motor3_enable);
    Serial.println("Motor3 Enabled");
    motor4.EnableRequest(motor4_enable);
    Serial.println("Motor4 Enabled");

    Serial.println("Waiting for HLFB...");
    if (motor1.EnableActiveLevel() == true) {
        unsigned long start1 = millis();
        while (motor1.HlfbState() != MotorDriver::HLFB_ASSERTED &&
            !motor1.StatusReg().bit.AlertsPresent &&
            millis() - start1 < 3000) {
            delay(10);
        }
    if (motor1.HlfbState() != MotorDriver::HLFB_ASSERTED) {
        Serial.println("Warning: Motor1 HLFB not asserted (not connected or not enabled)");
        }
    }
    if (motor2.EnableActiveLevel() == true) {
        unsigned long start2 = millis();
        while (motor2.HlfbState() != MotorDriver::HLFB_ASSERTED &&
            !motor2.StatusReg().bit.AlertsPresent &&
            millis() - start2 < 3000) {
            delay(10);
        }
    if (motor2.HlfbState() != MotorDriver::HLFB_ASSERTED) {
        Serial.println("Warning: Motor2 HLFB not asserted (not connected or not enabled)");
        }
    }
    if (motor3.EnableActiveLevel() == true) {
        unsigned long start3 = millis();
        while (motor3.HlfbState() != MotorDriver::HLFB_ASSERTED &&
            !motor3.StatusReg().bit.AlertsPresent &&
            millis() - start3 < 3000) {
            delay(10);
        }
    if (motor3.HlfbState() != MotorDriver::HLFB_ASSERTED) {
        Serial.println("Warning: Motor1 HLFB not asserted (not connected or not enabled)");
        }
    }
    if (motor4.EnableActiveLevel() == true) {
        unsigned long start4 = millis();
        while (motor4.HlfbState() != MotorDriver::HLFB_ASSERTED &&
            !motor1.StatusReg().bit.AlertsPresent &&
            millis() - start4 < 3000) {
            delay(10);
        }
    if (motor4.HlfbState() != MotorDriver::HLFB_ASSERTED) {
        Serial.println("Warning: Motor1 HLFB not asserted (not connected or not enabled)");
        }
    }

    // Check if motor alert occurred during enabling
    // Clear alert if configured to do so 
    if (motor1.StatusReg().bit.AlertsPresent) {
        Serial.println("Motor1 alert detected.");
        PrintAlerts();
        if (HANDLE_ALERTS) {
            HandleAlerts();
        } else {
            Serial.println("Enable automatic alert handling by setting HANDLE_ALERTS to 1.");
        }
        Serial.println("Enabling may not have completed as expected. Proceed with caution.");
        Serial.println();
    } else {
        Serial.println("Motor1 Ready");
    }

    if (motor2.StatusReg().bit.AlertsPresent) {
        Serial.println("Motor2 alert detected.");
        PrintAlerts();
        if (HANDLE_ALERTS) {
            HandleAlerts();
        } else {
            Serial.println("Enable automatic alert handling by setting HANDLE_ALERTS to 1.");
        }
        Serial.println("Enabling may not have completed as expected. Proceed with caution.");
        Serial.println();
    } else {
        Serial.println("Motor2 Ready");
    }

    if (motor3.StatusReg().bit.AlertsPresent) {
        Serial.println("Motor3 alert detected.");
        PrintAlerts();
        if (HANDLE_ALERTS) {
            HandleAlerts();
        } else {
            Serial.println("Enable automatic alert handling by setting HANDLE_ALERTS to 1.");
        }
        Serial.println("Enabling may not have completed as expected. Proceed with caution.");
        Serial.println();
    } else {
        Serial.println("Motor3 Ready");
    }

    if (motor4.StatusReg().bit.AlertsPresent) {
        Serial.println("Motor4 alert detected.");
        PrintAlerts();
        if (HANDLE_ALERTS) {
            HandleAlerts();
        } else {
            Serial.println("Enable automatic alert handling by setting HANDLE_ALERTS to 1.");
        }

        Serial.println("Enabling may not have completed as expected. Proceed with caution.");
        Serial.println();
    } else {
        Serial.println("Motor4 Ready");
    }
    delay(2000);
  } // End setup
//***********************************************************************
//***********************************************************************
void loop() {

   // Serial.println("Start Loop");
    currentMillis = millis(); // Used to calculate report interval

    ReadUdpData();
    //ReadSerialData();
    // ...rest of your loop code...

   // Look for a received packet.
    int packetSize = Udp.parsePacket();
    IPAddress remote = Udp.remoteIP();
    
    // Keep the connection alive.
    Ethernet.maintain();
    delay(10);
    UpdateMotorParameters();
  //**********************************************
  // State Engine for sequencing the motors
  //**********************************************
    if (next_step != next_step_last) {  // Update the State Enmgine step number when it changes
      //Serial.print("STATE_ENGINE:");
      sendStateEngineStep();
      next_step_last = next_step;
      if (Mode == 1){  // In Auto Mode load the next set of setpoints from the setpoints array
        loadSetpoints(next_step);  
      } //end if Mode
    } // end if next_step


    if (Mode == 0){  // 0 = Manual Mode move to using nmanual setpoints
        loadMotorSetpoints(); // 08/03/2025
      MoveAbsolutePosition(motor1, S1P_SPT, moveState1, moveStartTime1, lastMillis1, lastPosition1);
      MoveAbsolutePosition(motor2, S2P_SPT, moveState2, moveStartTime2, lastMillis2, lastPosition2);
      MoveAbsolutePosition(motor3, S3P_SPT, moveState3, moveStartTime3, lastMillis3, lastPosition3);
      MoveAbsolutePosition(motor4, S4P_SPT, moveState4, moveStartTime4, lastMillis4, lastPosition4);
    } //end if Mode

    if (Mode == 1) {  // if Mode is in Auto and Servo 1 is enabled start the sequence
       
        loadMotorSetpoints();
       
        if (currentMillis - lastReportDataTime >= ReportDataInterval) {
            Serial.println(S2V_SPT);
          }
       // if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, S1P_SPT, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
       // if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, S2P_SPT, moveState2, moveStartTime2, lastMillis2, lastPosition2);}
       //if (S3B1 == 1) {motor3Done = MoveAbsolutePosition(motor3, S2P_SPT, moveState3, moveStartTime3, lastMillis3, lastPosition3);}        
        //if (S3B1 == 1) {motor4Done = MoveAbsolutePosition(motor4, S4P_SPT, moveState4, moveStartTime4, lastMillis4, lastPosition4);}        
      
        switch (next_step) {
            case 0: // Idle
                //Serial.println("Step 0");
                S1V_SPT = 500;
                S2V_SPT = 500;
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryAddress, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryAddress, moveState2, moveStartTime2, lastMillis2, lastPosition2);}
                if (Start == 1) {  // Removed the semicolon
                    next_step = 1;
                }
                break;
            case 1: // Address
                //Serial.println("Step 1");
                //loadMotorSetpoints();
                //motor1Done = MoveDistance(motor1,2000);
                S2V_SPT = 0;
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryAddress, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryAddress, moveState2, moveStartTime2, lastMillis2, lastPosition2);}
                            
                if (motor1Done && motor2Done) {
                    next_step = 2;
                    moveState1 = MOVE_IDLE;  // Reset moveState1
                    moveState2 = MOVE_IDLE;  // Reset moveState2
                } 
                break;
            case 2: //Initial TakeAway
                //Serial.println("Step 2");

                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryTOS, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryTOS, moveState2, moveStartTime2, lastMillis2, lastPosition2);}
                                 
                if ((S1P <= S1P_SPT) &&  (S2P <= S2P_SPT)) {
                    next_step = 3;
                    //moveState1 = MOVE_IDLE;  // Reset moveState1
                    //moveState2 = MOVE_IDLE;  // Reset moveState2
                } 
                break;
            case 3: // Take Away
                //Serial.println("Step 3");
                //loadMotorSetpoints();
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryTOS, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryTOS, moveState2, moveStartTime2, lastMillis2, lastPosition2);}
                
                if ((S1P <= S1P_SPT) &&  (S2P <= S2P_SPT)) {
                    next_step = 4;
                    //moveState1 = MOVE_IDLE;  // Reset moveState1
                    //moveState2 = MOVE_IDLE;  // Reset moveState2
                } 
                break;
            case 4:  // Full Rotation              
                //Serial.println("Step 4");
                //loadMotorSetpoints();
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryTOS, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryTOS, moveState2, moveStartTime2, lastMillis2, lastPosition2);}

                if ((S1P <= S1P_SPT) &&  (S2P <= S2P_SPT)) {
                    next_step = 5;
                    //moveState1 = MOVE_IDLE;  // Reset moveState1
                    //moveState2 = MOVE_IDLE;  // Reset moveState2
                } 
                break;
            case 5:  // Top of Swing
                //Serial.println("Step 5");
                
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryTOS, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryTOS, moveState2, moveStartTime2, lastMillis2, lastPosition2);}

                if (motor1Done && motor2Done) {
                    next_step = 6;  // Reset to the initial step
                    moveState1 = MOVE_IDLE;  // Reset moveState1
                    moveState2 = MOVE_IDLE;  // Reset moveState2
                }
                break;
            case 6:  // Initial Downswing              
                //Serial.println("Step 6");
                
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryFinish, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryFinish, moveState2, moveStartTime2, lastMillis2, lastPosition2);}

                if ((S1P >= S1P_SPT) &&  (S2P >= S2P_SPT)) {
                    next_step = 7;
                    //moveState1 = MOVE_IDLE;  // Reset moveState1
                    //moveState2 = MOVE_IDLE;  // Reset moveState2
                }  
                break;
            case 7:  // Release             
                //Serial.println("Step 7");
                
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryFinish, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryFinish, moveState2, moveStartTime2, lastMillis2, lastPosition2);}

                if ((S1P >= S1P_SPT) &&  (S2P >= S2P_SPT)) {
                    next_step = 8;
                    //moveState1 = MOVE_IDLE;  // Reset moveState1
                    //moveState2 = MOVE_IDLE;  // Reset moveState2
                }   
                break;
            case 8:  // Impact             
                //Serial.println("Step 7");
                
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryFinish, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryFinish, moveState2, moveStartTime2, lastMillis2, lastPosition2);}

                if ((S1P >= S1P_SPT) &&  (S2P >= S2P_SPT)) {
                    next_step = 9;
                    //moveState1 = MOVE_IDLE;  // Reset moveState1
                    //moveState2 = MOVE_IDLE;  // Reset moveState2
                }  
                break;
            case 9:  // Follow Through        
                //Serial.println("Step 7");
                
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryFinish, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryFinish, moveState2, moveStartTime2, lastMillis2, lastPosition2);}

                if ((S1P >= S1P_SPT) &&  (S2P >= S2P_SPT)) {
                    next_step = 10;
                    //moveState1 = MOVE_IDLE;  // Reset moveState1
                    //moveState2 = MOVE_IDLE;  // Reset moveState2
                }  
                break;
            case 10:  // Finish           
                //Serial.println("Step 7");
                
                if (S1B1 == 1) {motor1Done = MoveAbsolutePosition(motor1, PrimaryFinish, moveState1, moveStartTime1, lastMillis1, lastPosition1);}
                if (S2B1 == 1) {motor2Done = MoveAbsolutePosition(motor2, SecondaryFinish, moveState2, moveStartTime2, lastMillis2, lastPosition2);}
              if (motor1Done && motor2Done) {
                  moveState1 = MOVE_IDLE;  // Reset moveState1
                  moveState2 = MOVE_IDLE;  // Reset moveState2
                  if (Repeat == 1) {                  
                      next_step = 1;  // Repeat mode goes back to step 1
                      Start = 0;
                      sendButtonStates();
                  } else {
                      next_step = 0;  // Single mode goes back to step 0
                      next_step = 0;  // Single mode goes back to step 0
                      Start = 0;
                      sendButtonStates();
                  }
              }

                break;
        } // end switch

    }  // end if (S1B2 == 1)
  //**********************************************
   // Serial.println("End Case Statement");
  //**********************************************
  
    //Periodically send the state engine step
    if (currentMillis - lastStateEngineStepTime > stateEngineStepInterval) {
        lastStateEngineStepTime = currentMillis;
        sendStateEngineStep();
    }

    unsigned long scanTime = calculateScanTime();
    // Periodically report debug data
    if (currentMillis - lastReportDataTime >= ReportDataInterval) {
        lastReportDataTime = currentMillis;
        // Calculate and print the scan time
        
        Serial.print("Scan time: ");
        Serial.print(scanTime);
        Serial.println(" ms");

        Serial.print("Mode =");
        Serial.print(Mode);
        Serial.print(" / ");
        Serial.print("S1V_SPT=");
        Serial.print(S1V_SPT); 
        Serial.print(" / ");  
        Serial.print("S1V=");
        Serial.print(S1V);
        Serial.print(" / "); 
        Serial.print("S1P_SPT=");
        Serial.println(S1P_SPT);

     /* Serial.print(" / ");
      Serial.print("S2V_SPT=");
      Serial.print(S2V_SPT);
      Serial.print(" / ");
      Serial.print("S2V=");
      Serial.print(S2V);
      Serial.print(" / ");
      Serial.print("S2P_SPT=");
      Serial.print(S2P_SPT);
      Serial.print(" / ");
      Serial.print("S2P=");
      Serial.print(S2P);
      Serial.print(" / ");
      Serial.println(" ");
      Serial.print("S2P_SPT - S2P = ");
      Serial.print(S2P_SPT - S2P);
      Serial.println(" / ");
      Serial.print("(S2P_SPT - S2P) * Velocity = ");
      Serial.print((S2P_SPT - S2P) * S1V);
      Serial.println(" / ");
      Serial.print("S1P_SPT - S1P = ");
      Serial.print(S1P_SPT - S1P);
      Serial.println(" / ");
      Serial.println(" ");
*/

   }
    // ...existing code...
}   // End loop

//********************************************************************
// Function definitions
//********************************************************************
void ReadUdpData() {
    int packetSize = Udp.parsePacket();
    if (packetSize > 0) {
        int bytesRead = Udp.read(packetReceived, MAX_PACKET_LENGTH);
        if (bytesRead > 0 && bytesRead < MAX_PACKET_LENGTH) {
            packetReceived[bytesRead] = 0; // Null-terminate
        } else {
            packetReceived[MAX_PACKET_LENGTH - 1] = 0; // Safety
        }
        String udpCommand = String(packetReceived);
        String prefix = "BOARD:" + String(BOARD_ID) + ";";
        if (udpCommand.startsWith(prefix)) {
            udpCommand = udpCommand.substring(prefix.length()); // Remove prefix
            handleCommand(udpCommand);
        }
        // Optionally, ignore or log commands not meant for this board
    }
}


//********************************************************************
void parseData(String data, int &V, int &A, int &P) {
    int firstComma = data.indexOf(',');
    int secondComma = data.indexOf(',', firstComma + 1);

    V = data.substring(0, firstComma).toInt();
    A = data.substring(firstComma + 1, secondComma).toInt();
    P = data.substring(secondComma + 1).toInt();
}
//********************************************************************
// read command string from HMI and parse command string
void handleCommand(String input) {
    input.trim(); // Remove whitespace and newlines
   
      // Special commands
    if (input == "CMD:REQUEST_VALUES") {
        //Serial.println("Debug 900 - Processing CMD:REQUEST_VALUES");
        sendCurrentValues();
        return;
    } else if (input == "CMD:REQUEST_BUTTON_STATES") {
        Serial.println("Debug 901 - Processing CMD:REQUEST_BUTTON_STATES");
        sendButtonStates();
        return;
    } else if (input == "CMD:REQUEST_SETPOINTS") {
        Serial.println("Debug 902 - Processing CMD:REQUEST_SETPOINTS");
        sendSetpoints();
        return;
    } else if (input == "CMD:REQUEST_STATE_ENGINE") {
        sendStateEngineStep();
        return;
    }

    // Remove "CMD:" prefix if present for custom commands
    String command = input;
    if (command.startsWith("CMD:")) {
        command = command.substring(4);
    }

    // Main command handling logic
    if (command == "Mode AUTO") {
        Mode = true;
        Serial.println("DATA: Auto Mode");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "Mode MANUAL") {
        Mode = false;
        Serial.println("DATA: Manual Mode");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "Repeat ENABLE" && !Repeat) {
        Repeat = true;
        Serial.println("DATA: Repeat enabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "Repeat DISABLE" && Repeat) {
        Repeat = false;
        Serial.println("DATA: Repeat disabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "Start ENABLE") {
        Start = true;
        Serial.println("DATA: Start enabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "Start DISABLE") {
        Start = false;
        Serial.println("DATA: Start disabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S1B1 ENABLE" && !S1B1) {
        S1B1 = true;
        Serial.println("Serial Available Flag3a");
        Serial.println("DATA:Servo1 Enabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S1B1 DISABLE" && S1B1) {
        S1B1 = false;
        Serial.println("Serial Available Flag4");
        Serial.println("DATA:Servo1 Disabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S1B2 Start" && !S1B2) {
        S1B2 = true;
        Serial.println("Serial Available Flag4a");
        Serial.println("DATA:Servo1 Started");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S1B2 STOP" && S1B2) {
        S1B2 = false;
        Serial.println("DATA:Servo1 Stopped");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command.startsWith("S1_Parameters:")) {
        parseData(command.substring(14), S1V_SPT, S1A_SPT, S1P_SPT);
        Serial.println("Serial Available Flag5");
        Serial.print("DATA:Parameters received - V:");
        Serial.print(S1V_SPT);
        Serial.print(" A:");
        Serial.print(S1A_SPT);
        Serial.print(" P:");
        Serial.println(S1P_SPT);
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S2B1 ENABLE" && !S2B1) {
        S2B1 = true;
        Serial.println("DATA:Servo2 Enabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S2B1 DISABLE" && S2B1) {
        S2B1 = false;
        Serial.println("DATA:Servo2 Disabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S2B2 Start" && !S2B2) {
        S2B2 = true;
        Serial.println("DATA:Servo2 Started");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S2B2 STOP" && S2B2) {
        S2B2 = false;
        Serial.println("DATA:Servo2 Stopped");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command.startsWith("S2_Parameters:")) {
        parseData(command.substring(14), S2V_SPT, S2A_SPT, S2P_SPT);
        Serial.print("DATA:Parameters received - V:");
        Serial.print(S2V_SPT);
        Serial.print(" A:");
        Serial.print(S2A_SPT);
        Serial.print(" P:");
        Serial.println(S2P_SPT);
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S3B1 ENABLE" && !S3B1) {
        S3B1 = true;
        Serial.println("DATA:Servo3 Enabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S3B1 DISABLE" && S3B1) {
        S3B1 = false;
        Serial.println("DATA:Servo3 Disabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S3B2 Start" && !S3B2) {
        S3B2 = true;
        Serial.println("DATA:Servo3 Started");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S3B2 STOP" && S3B2) {
        S3B2 = false;
        Serial.println("DATA:Servo3 Stopped");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command.startsWith("S3_Parameters:")) {
        parseData(command.substring(14), S3V_SPT, S3A_SPT, S3P_SPT);
        Serial.print("DATA:Parameters received - V:");
        Serial.print(S3V_SPT);
        Serial.print(" A:");
        Serial.print(S3A_SPT);
        Serial.print(" P:");
        Serial.println(S3P_SPT);
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S4B1 ENABLE" && !S4B1) {
        S4B1 = true;
        Serial.println("DATA:Servo4 Enabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S4B1 DISABLE" && S4B1) {
        S4B1 = false;
        Serial.println("DATA:Servo4 Disabled");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S4B2 Start" && !S4B2) {
        S4B2 = true;
        Serial.println("DATA:Servo4 Started");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command == "S4B2 STOP" && S4B2) {
        S4B2 = false;
        Serial.println("DATA:Servo4 Stopped");
        Serial.print("ACK:");
        Serial.println(command);
    }
    else if (command.startsWith("S4_Parameters:")) {
        parseData(command.substring(14), S4V_SPT, S4A_SPT, S4P_SPT);
        Serial.print("DATA:Parameters received - V:");
        Serial.print(S4V_SPT);
        Serial.print(" A:");
        Serial.print(S4A_SPT);
        Serial.print(" P:");
        Serial.println(S4P_SPT);
        Serial.print("ACK:");
        Serial.println(command);
    }
    else {
        Serial.print("ERR:Unknown command - ");
        Serial.println(command);
        if (Serial.available() > 0) {
            Serial.read();  // Flush the serial buffer
        }
    }
}
//********************************************************************
void sendCurrentValues() {
    String msg = "BOARD:" + String(BOARD_ID) + ";VALUES:";
    msg += String(S1V) + "," + String(S1A) + "," + String(S1P) + ",";
    msg += String(S2V) + "," + String(S2A) + "," + String(S2P) + ",";
    msg += String(S3V) + "," + String(S3A) + "," + String(S3P) + ",";
    msg += String(S4V) + "," + String(S4A) + "," + String(S4P);
    //Serial.print("Sending VALUES: "); Serial.println(msg);
        Udp.beginPacket(remoteIp, remotePort);
    Udp.write(msg.c_str());
    Udp.endPacket();
}

void sendButtonStates() {
    String msg = "BOARD:" + String(BOARD_ID) + ";BUTTON_STATES:";
    msg += (Mode ? "1" : "0"); msg += ",";
    msg += (Repeat ? "1" : "0"); msg += ",";
    msg += (Start ? "1" : "0"); msg += ",";
    msg += (S1B1 ? "1" : "0"); msg += ",";
    msg += (S1B2 ? "1" : "0"); msg += ",";
    msg += (S2B1 ? "1" : "0"); msg += ",";
    msg += (S2B2 ? "1" : "0"); msg += ",";
    msg += (S3B1 ? "1" : "0"); msg += ",";
    msg += (S3B2 ? "1" : "0"); msg += ",";
    msg += (S4B1 ? "1" : "0"); msg += ",";
    msg += (S4B2 ? "1" : "0");

    Udp.beginPacket(remoteIp, remotePort);
    Udp.write(msg.c_str());
    Udp.endPacket();
}

void sendSetpoints() {
    String msg = "BOARD:" + String(BOARD_ID) + ";SETPOINTS:";
    msg += String(S1V_SPT) + "," + String(S1A_SPT) + "," + String(S1P_SPT) + ",";
    msg += String(S2V_SPT) + "," + String(S2A_SPT) + "," + String(S2P_SPT) + ",";
    msg += String(S3V_SPT) + "," + String(S3A_SPT) + "," + String(S3P_SPT) + ",";
    msg += String(S4V_SPT) + "," + String(S4A_SPT) + "," + String(S4P_SPT);

    Udp.beginPacket(remoteIp, remotePort);
    Udp.write(msg.c_str());
    Udp.endPacket();

    // Optionally, also print to Serial with prefix
    Serial.print("BOARD:"); Serial.print(BOARD_ID); Serial.print(";SETPOINTS:");
    Serial.print(S1V_SPT); Serial.print(",");
    Serial.print(S1A_SPT); Serial.print(",");
    Serial.print(S1P_SPT); Serial.print(",");
    Serial.print(S2V_SPT); Serial.print(",");
    Serial.print(S2A_SPT); Serial.print(",");
    Serial.print(S2P_SPT); Serial.print(",");
    Serial.print(S3V_SPT); Serial.print(",");
    Serial.print(S3A_SPT); Serial.print(",");
    Serial.print(S3P_SPT); Serial.print(",");
    Serial.print(S4V_SPT); Serial.print(",");
    Serial.print(S4A_SPT); Serial.print(",");
    Serial.println(S4P_SPT);
}

void sendStateEngineStep() {
    String msg = "BOARD:" + String(BOARD_ID) + ";STATE_ENGINE:" + String(next_step);

    Udp.beginPacket(remoteIp, remotePort);
    Udp.write(msg.c_str());
    Udp.endPacket();

    Serial.print("BOARD:"); Serial.print(BOARD_ID); Serial.print(";STATE_ENGINE:");
    Serial.println(next_step);
}
//********************************************************************
//Motor Functions
//********************************************************************
void loadMotorSetpoints() {
    // Set the motor velocity and accleration to the setpoint values
    motor1.VelMax(S1V_SPT);
    motor1.AccelMax(S1A_SPT);
    motor2.VelMax(S2V_SPT);
    motor2.AccelMax(S2A_SPT);
    motor3.VelMax(S3V_SPT);
    motor3.AccelMax(S3A_SPT);
    motor4.VelMax(S4V_SPT);
    motor4.AccelMax(S4A_SPT);
}

//*************************************************
void loadSetpoints(int step) {
    
    if (step >= 0 && step <= 10) {

        S1V_SPT = motor1_setpoints[step][0] * KV1;
        S1A_SPT = motor1_setpoints[step][1] * KA1;
        S1P_SPT = motor1_setpoints[step][2] * KP1;   
       
        S2V_SPT = motor2_setpoints[step][0] * KV2;
        S2A_SPT = motor2_setpoints[step][1] * KA2;
        S2P_SPT = motor2_setpoints[step][2] * KP2;
 
        S3V_SPT = motor3_setpoints[step][0] * KV3;
        S3A_SPT = motor3_setpoints[step][1] * KA3;
        S3P_SPT = motor3_setpoints[step][2] * KP3;

        S4V_SPT = motor4_setpoints[step][0] * KV4;
        S4A_SPT = motor4_setpoints[step][1] * KA4;
        S4P_SPT = motor4_setpoints[step][2] * KP4;

    }
    sendSetpoints();
} // End LoadSetpoints

//*******************************************************
int Calculate_Velocity(int POS1, int SPT1, int POS2, int SPT2, int Velocity1) {
  int Velocity2;
  //Velocity2 = abs(((SPT2 - POS2) * Velocity1) / (SPT1 - POS1));
  Velocity2 = abs(SPT2 - POS2);
  
  if (Velocity2 > 5000) {
    Velocity2 = 5000;
  }
 // if (Velocity2 <= 200) {
 //   Velocity2 = 200;
 //}
  return Velocity2;
}

//*******************************************************

void UpdateMotorParameters () {
    motor1_enable = digitalRead(inputPin1);
    motor1.EnableRequest(motor1_enable);
    motor2_enable = digitalRead(inputPin2);
    motor2.EnableRequest(motor2_enable);
    motor3_enable = digitalRead(inputPin3);
    motor3.EnableRequest(motor3_enable);
    motor4_enable = digitalRead(inputPin4);
    motor4.EnableRequest(motor4_enable);
    
    // Read the motors current Velocity
    S1V = motor1.VelocityRefCommanded();
    S2V = motor2.VelocityRefCommanded();
    S3V = motor3.VelocityRefCommanded();
    S4V = motor4.VelocityRefCommanded();

    // Read the motors current Position
    S1P = motor1.PositionRefCommanded();
    S2P = motor2.PositionRefCommanded();
    S3P = motor3.PositionRefCommanded();
    S4P = motor4.PositionRefCommanded();

}  // end UpdateMotorParameters

//********************************************************************
//  MoveDistance (relative movement)
//********************************************************************
bool MoveAbsolutePosition(MotorDriver &motor, int position, MoveState &moveState, unsigned long &moveStartTime, unsigned long &lastMillis, int &lastPosition) {
    switch (moveState) {
        case MOVE_IDLE:
           /* if (motor.StatusReg().bit.AlertsPresent) {
                Serial.println("Motor alert detected.");
                PrintAlerts();
                if (HANDLE_ALERTS) {
                    HandleAlerts();
                } else {
                    Serial.println("Enable automatic alert handling by setting HANDLE_ALERTS to 1.");
                }
                Serial.println("Move canceled.");
                Serial.println();
                moveState = MOVE_DONE;
                return false;
            }
            */
            if (!motor.EnableRequest()) {
                Serial.println("Motor is not enabled. Enabling motor.");
                motor.EnableRequest(true);
                delay(100);  // Small delay to ensure motor is enabled
            }
            //Serial.print("Moving to absolute position: ");
            //Serial.println(position);
            //delay(100);
            motor.Move(position, MotorDriver::MOVE_TARGET_ABSOLUTE);
            //Serial.println("Moving.. Waiting for HLFB");
            
            //delay(100);
            moveStartTime = millis();
            moveState = MOVE_WAIT_HLFB;
            // Store initial position when starting a move
            lastPosition = motor.StepsComplete();
            lastMillis = millis();
            break;

        case MOVE_WAIT_HLFB:
        
            if (motor.StepsComplete() && motor.HlfbState() == MotorDriver::HLFB_ASSERTED) {
                
                moveState = MOVE_DONE;
                //Serial.println("Move Done");
                return true;
            }
            /*if (motor.StatusReg().bit.AlertsPresent) {
                Serial.println("Motor alert detected.");
                PrintAlerts();
                if (HANDLE_ALERTS) {
                    HandleAlerts();
                } else {
                    Serial.println("Enable automatic fault handling by setting HANDLE_ALERTS to 1.");
                }
                Serial.println("Motion may not have completed as expected. Proceed with caution.");
                Serial.println();
                moveState = MOVE_DONE;
                return false;
            }
           
            if (millis() - moveStartTime > moveTimeout) {
                Serial.println("Move timeout.");
                moveState = MOVE_DONE;
                return false;
            }
             */
            break;

        case MOVE_DONE:
            moveState = MOVE_IDLE;
            return true;
    }
    return false;
}
//********************************************************************

void PrintAlerts() {
    MotorDriver* motors[] = {&motor1, &motor2, &motor3, &motor4};
    const char* motorNames[] = {"Motor1", "Motor2", "Motor3", "Motor4"};
    
    for (int i = 0; i < 4; ++i) {
        Serial.print(motorNames[i]);
        Serial.println(" alerts present: ");
        if (motors[i]->AlertReg().bit.MotionCanceledInAlert) {
            Serial.println("    MotionCanceledInAlert ");
        }
        if (motors[i]->AlertReg().bit.MotionCanceledPositiveLimit) {
            Serial.println("    MotionCanceledPositiveLimit ");
        }
        if (motors[i]->AlertReg().bit.MotionCanceledNegativeLimit) {
            Serial.println("    MotionCanceledNegativeLimit ");
        }
        if (motors[i]->AlertReg().bit.MotionCanceledSensorEStop) {
            Serial.println("    MotionCanceledSensorEStop ");
        }
        if (motors[i]->AlertReg().bit.MotionCanceledMotorDisabled) {
            Serial.println("    MotionCanceledMotorDisabled ");
        }
        if (motors[i]->AlertReg().bit.MotorFaulted) {
            Serial.println("    MotorFaulted ");
        }
    }
}
//********************************************************************
void HandleMotorAlerts(MotorDriver &motor, const char *motorName) {
    if (motor.AlertReg().bit.MotorFaulted) {
        Serial.println(String(motorName) + " Faults present. Cycling enable signal to motor to clear faults.");
        motor.EnableRequest(false);
        delay(10);
        motor.EnableRequest(true);
    }
}
//********************************************************************
void HandleAlerts() {
    MotorDriver* motors[] = {&motor1, &motor2, &motor3, &motor4};
    const char* motorNames[] = {"Motor1", "Motor2", "Motor3", "Motor4"};
    
    for (int i = 0; i < 4; ++i) {
        HandleMotorAlerts(*motors[i], motorNames[i]);
    }
    
    Serial.println("Clearing alerts.");
    for (int i = 0; i < 4; ++i) {
        motors[i]->ClearAlerts();
    }
}
//********************************************************************
// Function to calculate scan time
unsigned long calculateScanTime() {
    static unsigned long lastTime = 0;
    unsigned long currentTime = millis();
    unsigned long scanTime = currentTime - lastTime;
    lastTime = currentTime;
    return scanTime;
}

