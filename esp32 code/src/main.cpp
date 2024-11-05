#include "Wire.h" // I2C -- protocol used for the IMU
#include <SPI.h>  // SPI -- protocol used for the SD Card
#include "SPIFFS.h"
#include <string>

using namespace std;


// Name of the file to be created and saved to the SD Card
const char * FILE_NAME = "/data.csv";



// a counter for number of records collected
static int totalRecords = 0;

// constants to help with the frequency of data collection
static const int IMU_HZ = 50;
static const int RECORD_COUNT = IMU_HZ; // one sec
static const int DESIRED_DELAY = 1000 / IMU_HZ;

// a variable to store the time (in uptime milliseconds)
static int epochTime = 0;



unsigned long startTime;
unsigned long endTime;
int last20;

void setup() {
  // put your setup code here, to run once:
  // start serial (for print statements)
  Serial.begin(9600);
  Serial.println("Start");
  //FILE_NAME = "/data.csv" + to_string(millis());




  
  

 if(!SPIFFS.begin(true)){
    Serial.println("An Error has occurred while mounting SPIFFS");
    return;
  }
  
  /* Create the file to store data
  
  NOTE: this file will be overwritten with each power cycle.
  We first write the headers of the CSV file.

  */

  File dataFile = SPIFFS.open(FILE_NAME, FILE_WRITE);
  SPIFFS.remove(FILE_NAME);
  dataFile = SPIFFS.open(FILE_NAME, FILE_WRITE);

  // write the headers
  dataFile.println("time_ms,pointer,middle,ring,ecg");
  dataFile.close();
}

void loop() {  
  

  // setup LED
  digitalWrite(LED_BUILTIN, HIGH);
  
  // initialize arrays to store batch of data\
  // time
  int msTimeArray[RECORD_COUNT];
  
  
  int pointerFinger[RECORD_COUNT];  
  int middleFinger[RECORD_COUNT];
  int ringFinger[RECORD_COUNT];
  int ecg[RECORD_COUNT];
  

  for(int i = 0; i < RECORD_COUNT; i++)
  {
    // current uptime in milliseconds
    int startMs = millis();

    // initialize epoch if zero (first pass)
    if ( epochTime == 0 ) { 
      epochTime = startMs; 
      last20=startMs;
    }
   

    // record epoch offset
    msTimeArray[i] = startMs - epochTime;
    
    // store acceleration data
    pointerFinger[i] = analogRead(4);
    middleFinger[i] = analogRead(5);
    ringFinger[i] = analogRead(6);
    ecg[i] = analogRead(7);
    //Serial.println(pointerFinger[i]);
    

   
   
    // delay to match desired hz
    int duration = millis() - startMs;
    if ( duration < DESIRED_DELAY ) {
      delay(DESIRED_DELAY - duration);
    }
  }
   
  // write the batch to the file.
  File dataFile = SPIFFS.open(FILE_NAME, FILE_APPEND);
  if (dataFile) {
    for (int j=0; j<RECORD_COUNT; j++) {
      dataFile.print(msTimeArray[j]);
      dataFile.print(",");
      dataFile.print(pointerFinger[j]);
      dataFile.print(",");
      dataFile.print(middleFinger[j]);
      dataFile.print(",");
      dataFile.print(ringFinger[j]);
      dataFile.print(",");
      dataFile.println(ecg[j]);
    }
  }
  dataFile.close();
  
  // LED would blink (red) after each successful file write
  digitalWrite(LED_BUILTIN, LOW);
}