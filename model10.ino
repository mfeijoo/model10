#include <ADS1115_WE.h>
#include <SPI.h>
#include <Wire.h>
#include "Adafruit_MCP9808.h"

ADS1115_WE adc(0x48);

Adafruit_MCP9808 tempsensor = Adafruit_MCP9808();

//definitions model 10
#define CS_ADQ1 A5
#define CS_ADQ0 2
#define RST A2
#define HOLD A3
#define SHD_PS 11
#define RAN_1 9
#define RAN_2 A4
#define RAN_3 A1
#define RAN_4 A0
#define SHD_REF 7
#define CS_POT 10
#define PSFC 16.4362
#define testpin 13

// For AD51115 powers
int16_t adc0 = 0;
int16_t adc1 = 0;
int16_t adc2 = 0;
int16_t adc3 = 0;
float adc0V = 0.0000;
float adc1V = 0.0000;
float adc2V = 0.0000;
float adc3V = 0.0000;

int integral = 300;
unsigned long integraltimemicros = 1000;
int resettimemicros = 70;

unsigned long previousmillis = 0;
unsigned long initialintegralmicros = 0;
unsigned long integralmicros = 0;
unsigned long startmicros = 0;
int count = 0;

//pot value in counts from 0 to 1023
int potlow;
int pothigh;
int potnow = 1;

float setvolt = 56.56;
float PSV;

float temp = 27;

//darkcurrents
unsigned int dcvch[] = {5000, 3000};
unsigned int dcvchmax[] = {6553, 65535};
unsigned int dcvchmin[] = {0, 0};

unsigned int chb[] = {0, 0};
float chv[] = {0.0, 0.0};


void setup() {
  
  //all pins output
  pinMode(CS_ADQ1, OUTPUT);
  pinMode(CS_ADQ0, OUTPUT);
  pinMode(RST, OUTPUT);
  pinMode(HOLD, OUTPUT);
  pinMode(SHD_PS, OUTPUT);
  pinMode(RAN_1, OUTPUT);
  pinMode(RAN_2, OUTPUT);
  pinMode(RAN_3, OUTPUT);
  pinMode(RAN_4, OUTPUT);
  pinMode(SHD_REF, OUTPUT);
  pinMode(CS_POT, OUTPUT);
  pinMode(testpin, OUTPUT);

  digitalWrite(CS_ADQ0, HIGH);
  digitalWrite(RST, HIGH);
  digitalWrite(HOLD, LOW);
  digitalWrite(CS_ADQ1, HIGH);
  digitalWrite(SHD_PS, LOW);
  digitalWrite(SHD_REF, LOW);
  digitalWrite(RAN_1, LOW);
  digitalWrite(RAN_2, LOW);
  digitalWrite(RAN_3, LOW);
  digitalWrite(RAN_4, HIGH);
  digitalWrite(CS_POT, HIGH);
  

  Serial.begin(250000);
  Wire.begin();
  SPI.begin();

  //Turn on the reference of the DAC
  Wire.beginTransmission(0x0F);
  Wire.write(0x38);
  Wire.write(0x0);
  Wire.write(0x1);
  Wire.endTransmission();


  tempsensor.begin(0x18); //this line on
  tempsensor.setResolution(3); //this line on
  // Mode Resolution SampleTime
  //  0    0.5°C       30 ms
  //  1    0.25°C      65 ms
  //  2    0.125°C     130 ms
  //  3    0.0625°C    250 ms
  tempsensor.wake(); //this line on

  Wire.setClock(400000);

  //Settting the newPOT for the first time
  //newpotcount = (int)(((4020/(setvolt - 10)) - 80)*102.3);
  //newpotcount = 400;
  SPI.beginTransaction(SPISettings(50000000, MSBFIRST, SPI_MODE1));
  //Remove protection from the new potentiometer
  digitalWrite(CS_POT, LOW);
  SPI.transfer16(0x1c02);
  digitalWrite(CS_POT, HIGH);
  SPI.endTransaction();

  //wait 100 milliseconds and turn on the reference
  delay(100);
  digitalWrite(SHD_REF, HIGH);
  
  //Then wait 2 seconds and turn on the Power Suplly
  delay(2000);
  digitalWrite (SHD_PS, HIGH);

  //Set the pot for the first time
  setpot(300);
  

  
  //Set range of all channels to +-3 * Vref
  SPI.beginTransaction(SPISettings(66670000, MSBFIRST, SPI_MODE0));
  digitalWrite(CS_ADQ0, LOW);
  SPI.transfer16(0b1101000000010100);
  SPI.transfer16(0b0000000000000000);
  digitalWrite(CS_ADQ0, HIGH);
  digitalWrite(CS_ADQ1, LOW);
  SPI.transfer16(0b1101000000010100);
  SPI.transfer16(0b0000000000000000);
  digitalWrite(CS_ADQ1, HIGH);
  SPI.endTransaction();
  

  //regulatePS(); //at the begining regulate PS
  //sdc(); //at the begining subtract dark current
  //setpot(700);

  adc.setConvRate(ADS1115_860_SPS);
  
}

void loop() {

  if (micros() - initialintegralmicros >= integraltimemicros){
    


    ReadChannelsOncetempandsend();

    /*//digitalWrite(testpin, HIGH);
    adc.setVoltageRange_mV(ADS1115_RANGE_6144);
    adc.setCompareChannels(ADS1115_COMP_0_GND);
    adc.startSingleMeasurement();
    adc.startSingleMeasurement();
    while(adc.isBusy()){
      ReadChannelsOncetempandsend();
      }
    adc0 = adc.getRawResult();
    //float adc0V = adc.getResult_V();
    //digitalWrite(testpin, LOW);
 

    adc.setCompareChannels(ADS1115_COMP_1_GND);
    adc.startSingleMeasurement();
    adc.startSingleMeasurement();
    while(adc.isBusy()){
      ReadChannelsOncetempandsend();
      }
    adc1 = adc.getRawResult();
    //adc1V = adc.getResult_V() * 16.2985;
    
    adc.setCompareChannels(ADS1115_COMP_2_GND);
    adc.startSingleMeasurement();
    adc.startSingleMeasurement();
    while(adc.isBusy()){
      ReadChannelsOncetempandsend();
      }
    adc2 = adc.getRawResult();
    //adc2V = adc.getResult_V() * -4.6529;

    adc.setVoltageRange_mV(ADS1115_RANGE_2048);
    adc.setCompareChannels(ADS1115_COMP_3_GND);
    adc.startSingleMeasurement();
    adc.startSingleMeasurement();
    while(adc.isBusy()){
      ReadChannelsOncetempandsend();
      }
    adc3 = adc.getRawResult();
    //adc3V = adc.getResult_V();
    //digitalWrite(testpin, LOW);*/
  }




  if (Serial.available() > 0) {
    char inChar = (char)Serial.read();
    
    
    if (inChar == 'r'){
      String PSs = Serial.readStringUntil(',');
      char comma = Serial.read(); //discard comma at the end
      Serial.println(PSs.toFloat(), 2);
      setvolt = PSs.toFloat();
      regulatePS();
    }

    if (inChar == 'c'){
      String rangonstr = Serial.readStringUntil(',');
      char comma = Serial.read();
      int rangon = rangonstr.toInt();
      Serial.print("Capacitor Rango number ");
      Serial.print(rangon);
      Serial.println (" turned on");
      switch (rangon){
        case 1:
          digitalWrite(RAN_1, HIGH);
          digitalWrite(RAN_2, LOW);
          digitalWrite(RAN_3, LOW);
          digitalWrite(RAN_4, LOW);
          break;
        case 2:
          digitalWrite(RAN_1, LOW);
          digitalWrite(RAN_2, HIGH);
          digitalWrite(RAN_3, LOW);
          digitalWrite(RAN_4, LOW);
          break;
        case 3:
          digitalWrite(RAN_1, LOW);
          digitalWrite(RAN_2, LOW);
          digitalWrite(RAN_3, HIGH);
          digitalWrite(RAN_4, LOW);
          break;
        case 4:
          digitalWrite(RAN_1, LOW);
          digitalWrite(RAN_2, LOW);
          digitalWrite(RAN_3, LOW);
          digitalWrite(RAN_4, HIGH);
          break;
      }
      delay(500);
    }
    
    if (inChar == 's'){
     sdc();
    }

    if (inChar == 't'){
      startmicros = micros();
      count = 0;
    }

    if (inChar == 'd'){
      String ch = Serial.readStringUntil(',');
      //char comma = Serial.read();
      String dcvalue = Serial.readStringUntil(',');
      char comma2 = Serial.read();
      setvoltdc(ch.toInt(), dcvalue.toInt());
      Serial.print("Dark Current of ch ");
      Serial.print(ch);
      Serial.print(" set to ");
      Serial.println(dcvalue);
    }
     
     if (inChar == 'w'){
      char ps = (char)Serial.read();
      if (ps == '1'){
        //Activate Power Supply
        Serial.println("PS ON");
        digitalWrite (SHD_PS, HIGH);
       }
      if (ps == '0'){
        //Dectivate Power Supply
        Serial.println("PS OFF");
        digitalWrite (SHD_PS, LOW);
      }
    }
  }
}


void ReadChannels() {
  //digitalWrite(testpin, HIGH);
  SPI.beginTransaction(SPISettings(66670000, MSBFIRST, SPI_MODE0));
  digitalWrite(CS_ADQ0, LOW);
  chb[0] = SPI.transfer16(0b1101000000010000);
  SPI.transfer16(0b0000000000000000);
  digitalWrite(CS_ADQ0, HIGH);
  //digitalWrite(testpin, LOW);
  SPI.endTransaction();

  SPI.beginTransaction(SPISettings(66670000, MSBFIRST, SPI_MODE0));
  digitalWrite(CS_ADQ1, LOW);
  chb[1] = SPI.transfer16(0b1101000000010000);
  SPI.transfer16(0b0000000000000000);
  digitalWrite(CS_ADQ1, HIGH);
  SPI.endTransaction();

  //chv[0] = -(chb[0] * 24.576/65535) + 12.288;
  //chv[1] = -(chb[1] * 24.576/65535) + 12.288;
  
}

void ReadChannelsOncetempandsend(){
   
   ReadChannelsOnce();

  //while it is integrating
  //read temp and send to serial

  //digitalWrite(testpin, HIGH);
  //temp = tempsensor.readTempC();
  //digitalWrite(testpin, LOW);


    //digitalWrite(testpin, HIGH);
    Serial.print(initialintegralmicros - startmicros);
    //Serial.print(",");
    //Serial.print(temp, 4);
    Serial.print(",");
    Serial.print(count);
    Serial.print(",");
    Serial.print(chb[0]);
    Serial.print(",");
    Serial.println(chb[1]);
    //Serial.print(",");
    
    //adc0 5V
    //Serial.print(adc0);
    //Serial.print(",");
    //adc1 PS
    //Serial.print(adc1);
    //Serial.print(",");
    //adc2 -15
    //Serial.print(adc2);
    //Serial.print(",");
    //adc3 ref 1.25V
    //Serial.println(adc3);
    //digitalWrite(testpin, LOW);
    count = count + 1;

  
}

void ReadChannelsOnce() {
  
  //digitalWrite(testpin, HIGH);
  //hold starts
  digitalWrite(HOLD, HIGH);
  delayMicroseconds(10);
  ReadChannels();
  
  //digitalWrite (testpin, LOW);
  //reset the integration and a new integration process starts
  digitalWrite (RST, LOW);
  delayMicroseconds (resettimemicros);
  digitalWrite (RST, HIGH);
  delayMicroseconds(5);
  //Hold ends
  digitalWrite (HOLD, LOW);
  //digitalWrite (testpin, HIGH);
  initialintegralmicros = micros();
}


void setvoltdc(int ch, unsigned int dcvch){
  Wire.beginTransmission(0x0F);
  Wire.write(24 + ch);
  Wire.write(dcvch >> 8);
  Wire.write(dcvch & 0xFF);
  Wire.endTransmission();
}

void regulatePS(){
  //measure PS once
  //potlow = 0;
  //pothigh = 1023;
  potnow = 255;
  setpot(potnow);
  delay (1000);
  readPS();


  while (!((PSV <= (setvolt + 0.008)) && (PSV >= (setvolt - 0.008)))){
    if (Serial.available() > 0) {
    char inChar = (char)Serial.read();
        if (inChar == 'n'){
          break;
        }
    }
    
    //voltage is too high
    if (PSV > (setvolt + 0.008)){
      //pothigh = potnow;
      potnow = potnow - 1;
    }
    //voltage is too low
    else if (PSV < (setvolt - 0.008)){
      //potlow = potnow;
      potnow = potnow + 1;
    }
    //potnow = int((potlow + pothigh) / 2);
    setpot(potnow);
    readPS();
    Serial.print("setvolt,");
    Serial.print(setvolt, 2);
    //Serial.print(",pothigh,");
    //Serial.print(pothigh);
    Serial.print(",potnow,");
    Serial.print(potnow);
    //Serial.print(",potlow,");
    //Serial.print(potlow);
    Serial.print(",PS,");
    Serial.println(PSV, 4);
    //digitalWrite (ledpin, HIGH);

  }
}

void readPS(){
  adc.setVoltageRange_mV(ADS1115_RANGE_6144);
  adc.setCompareChannels(ADS1115_COMP_1_GND);
  adc.startSingleMeasurement();
  while(adc.isBusy()){}
  PSV = adc.getResult_V() * 16.2985;
}

void setpot(int x) {
  SPI.beginTransaction(SPISettings(50000000, MSBFIRST, SPI_MODE1));
  //set the pot
  digitalWrite(CS_POT, LOW);
  SPI.transfer16(0x400 | x);
  digitalWrite(CS_POT, HIGH);
  SPI.endTransaction();
  delay(1000);
}



//function to substract dark current
void sdc(){
 unsigned int dcvch[] = {32767, 32767};
 unsigned int dcvchmax[] = {65535, 65535};
 unsigned int dcvchmin[] = {0, 0};
 for (int i = 0; i < 2; i++){
  dcvch[i] = (dcvchmin[i] + dcvchmax[i])/2;
  setvoltdc(i, dcvch[i]);
  while (micros() - initialintegralmicros < integralmicros){}
  ReadChannelsOnce();
  Serial.print(i);
  Serial.print(",dcvchmin,");
  Serial.print(dcvchmin[i]);
  Serial.print(",dcvch,");
  Serial.print(dcvch[i]);
  Serial.print(",dcvchmax,");
  Serial.print(dcvchmax[i]);
  Serial.print(",chv,");
  Serial.println(chv[i], 4);
  while (micros() - initialintegralmicros < integralmicros){}
  ReadChannelsOnce();
  
  while (!((chv[i] <= -0.0005) && (chv[i] >= 0.0005))){
   if (dcvchmax[i] - dcvchmin[i] == 1){
    break;
   }
   if (chv[i] < -0.0005){ 
    dcvchmax[i] = dcvch[i];
   }
   if (chv[i] > 0.0005){
    dcvchmin[i] = dcvch[i];
   }
   dcvch[i] = int((dcvchmin[i] + dcvchmax[i])/2);
   setvoltdc(i, dcvch[i]);
   while (millis() - previousmillis < integral){ 
   }
   ReadChannelsOnce();
   Serial.print(i);
   Serial.print(",dcvchmin,");
   Serial.print(dcvchmin[i]);
   Serial.print(",dcvch,");
   Serial.print(dcvch[i]);
   Serial.print(",dcvchmax,");
   Serial.print(dcvchmax[i]);
   Serial.print(",chv,");
   Serial.println(chv[i], 4);
   while (millis() - previousmillis < integral){ 
   }
   ReadChannelsOnce(); 
  }
 }
}
