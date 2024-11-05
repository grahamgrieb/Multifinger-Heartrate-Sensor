#include <Adafruit_TinyUSB.h> // required to print serial over USB
#include "LSM6DS3.h" // IMU library
#include "Wire.h" // I2C -- protocol used for the IMU
#include <U8x8lib.h>  //Display library
#include <SPI.h>  // SPI -- protocol used for the SD Card
#include "SdFat.h" // SD library
#include "sdios.h" // SD Card support (input/output, eg., files)

// !!! This code Assume SD Card is formatted FAT32 !!!

// Seeed Studio Extension Board uses Pin 2 for the SD Card
#define SD_CS_PIN D2  
// Name of the file to be created and saved to the SD Card
#define FILE_NAME "data.csv"

SdFat SD;

// a counter for number of records collected
static int totalRecords = 0;

// constants to help with the frequency of data collection
static const int IMU_HZ = 100;
static const int RECORD_COUNT = IMU_HZ; // one sec
static const int DESIRED_DELAY = 1000 / IMU_HZ;

// a variable to store the time (in uptime milliseconds)
static int epochTime = 0;

// initialized the OLED
U8X8_SSD1306_128X64_NONAME_HW_I2C u8x8(/* clock=*/PIN_WIRE_SCL, /* data=*/PIN_WIRE_SDA, /* reset=*/U8X8_PIN_NONE);  // OLEDs without Reset of the Display


unsigned long startTime;
unsigned long endTime;
int last20;

void setup() {
  // put your setup code here, to run once:
  // start serial (for print statements)
  Serial.begin(9600);
  Serial.println("Start");

  // initialize the OLED
  u8x8.begin();
  pinMode(LED_BUILTIN, OUTPUT);
  u8x8.setFlipMode(1); 

  // clear the OLED
  u8x8.setFont(u8x8_font_chroma48medium8_r);
  u8x8.clear();

  
  
  // initialize the SD Card
  Wire.begin();
  if (!SD.begin(SD_CS_PIN)) {
    Serial.println("initialization failed!");
    return;
  }
  
  /* Create the file to store data
  
  NOTE: this file will be overwritten with each power cycle.
  We first write the headers of the CSV file.

  */
  File dataFile = SD.open(FILE_NAME, FILE_WRITE);
  dataFile.remove();
  dataFile.close();
  dataFile = SD.open(FILE_NAME, FILE_WRITE);

  // write the headers
  dataFile.println("time_ms,pointer,middle,ring,ecg");
  dataFile.close();
}

void loop() {  
  
  // write OLED
  u8x8.setCursor(0, 0);
  u8x8.print("ECG + PPG");
  
  // setup LED
  digitalWrite(LED_BUILTIN, HIGH);
  
  // initialize arrays to store batch of data\
  // time
  int msTimeArray[RECORD_COUNT];
  
  
  int pointerFinger[RECORD_COUNT];  
  int middleFinger[RECORD_COUNT];
  int ringFinger[RECORD_COUNT];
  int pinkieFinger[RECORD_COUNT];
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
    pointerFinger[i] = analogRead(0);
    middleFinger[i] = analogRead(1);
    ringFinger[i] = analogRead(2);
    ecg[i] = analogRead(3);
    //Serial.println(pointerFinger[i]);
    

   
    // print record count to screen (updated every 20 records)
    if ( i % 20  == 0)
    {
      u8x8.setCursor(0, 12);
      u8x8.print("recs: ");
      u8x8.println(totalRecords);
      totalRecords += 20;

    }

    // delay to match desired hz
    int duration = millis() - startMs;
    if ( duration < DESIRED_DELAY ) {
      delay(DESIRED_DELAY - duration);
    }
  }
   
  // write the batch to the file.
  File dataFile = SD.open(FILE_NAME, FILE_WRITE);
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