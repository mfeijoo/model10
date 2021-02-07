

//master branch file

#include <SPI.h>
#include <Wire.h>
#include "Adafruit_MCP9808.h"

Adafruit_MCP9808 tempsensor = Adafruit_MCP9808();

//definitions model 10
#define SLT A5
#define CS_ADQ 2
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

// For AD51115 powers
int16_t adc0;
int16_t adc1;
int16_t adc2;
int16_t adc3;

int integral = 300;
int resettime = 70;

unsigned long previousMillis = 0;

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
  pinMode(SLT, OUTPUT);
  pinMode(CS_ADQ, OUTPUT);
  pinMode(RST, OUTPUT);
  pinMode(HOLD, OUTPUT);
  pinMode(SHD_PS, OUTPUT);
  pinMode(RAN_1, OUTPUT);
  pinMode(RAN_2, OUTPUT);
  pinMode(RAN_3, OUTPUT);
  pinMode(RAN_4, OUTPUT);
  pinMode(SHD_REF, OUTPUT);
  pinMode(CS_POT, OUTPUT);

  digitalWrite(SLT, LOW);
  digitalWrite(RST, HIGH);
  digitalWrite(HOLD, LOW);
  digitalWrite(CS_ADQ, HIGH);
  digitalWrite(SHD_PS, LOW);
  digitalWrite(SHD_REF, LOW);
  digitalWrite(RAN_1, LOW);
  digitalWrite(RAN_2, HIGH);
  digitalWrite(RAN_3, LOW);
  digitalWrite(RAN_4, LOW);
  digitalWrite(CS_POT, HIGH);
  

  Serial.begin (115200);
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
  digitalWrite(CS_ADQ, LOW);
  SPI.transfer16(0b1101000000010100);
  SPI.transfer16(0b0000000000000000);
  digitalWrite(CS_ADQ, HIGH);
  SPI.endTransaction();
  

  //regulatePS(); //at the begining regulate PS
  //sdc(); //at the begining subtract dark current
  //setpot(700);
  
}

void loop() {  

  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= integral) {


    ReadChannelsOnce();


    //while integration is happening
    //we collect the rest of the CDA power values
    //collect the temperature and send everything via serial

    Wire.beginTransmission(0x48);
    Wire.write(0b00000001);
    Wire.write(0b01000000);
    Wire.write(0b11100010);
    Wire.endTransmission();
    Wire.beginTransmission(0x48);
    Wire.write(0b00000000);
    Wire.endTransmission();
    delay(5);
    Wire.requestFrom(0x48, 2);
    adc0 = (Wire.read() << 8 | Wire.read());

    Wire.beginTransmission(0x48);
    Wire.write(0b00000001);
    Wire.write(0b01010000);
    Wire.write(0b11100010);
    Wire.endTransmission();
    Wire.beginTransmission(0x48);
    Wire.write(0b00000000);
    Wire.endTransmission();
    delay(5);
    Wire.requestFrom(0x48, 2);
    adc1 = (Wire.read() << 8 | Wire.read());

    Wire.beginTransmission(0x48);
    Wire.write(0b00000001);
    Wire.write(0b01100000);
    Wire.write(0b11100010);
    Wire.endTransmission();
    Wire.beginTransmission(0x48);
    Wire.write(0b00000000);
    Wire.endTransmission();
    delay(5);
    Wire.requestFrom(0x48, 2);
    adc2 = (Wire.read() << 8 | Wire.read());

    Wire.beginTransmission(0x48);
    Wire.write(0b00000001);
    Wire.write(0b01110100);
    Wire.write(0b11100010);
    Wire.endTransmission();
    Wire.beginTransmission(0x48);
    Wire.write(0b00000000);
    Wire.endTransmission();
    delay(5);
    Wire.requestFrom(0x48, 2);
    adc3 = (Wire.read() << 8 | Wire.read());


    temp = tempsensor.readTempC();


    Serial.print(currentMillis);
    Serial.print(",");
    Serial.print(temp, 4);
    Serial.print(",");
    Serial.print(chv[0], 4);
    Serial.print(",");
    Serial.print(chv[1], 4);
    Serial.print(",");
    
    //adc0 5V
    //para probar en Arduino
    Serial.print(adc0 * 0.1875 / 1000, 4);
    //Serial.print(adc0);
    Serial.print(",");
    //adc1 PS
    //to test with Arduino
    Serial.print(adc1 * 0.1875 / 1000 * PSFC, 4);
    //Serial.print(adc1); //never use this option 1 file per box
    Serial.print(",");
    //adc2 -15
    //para probar en Arduino
    Serial.print(adc2 * 0.1875 / 1000 * -4.7024, 4);
    //Serial.print(adc2);
    Serial.print(",");
    //adc3 ref 1.25V
    //para probar en Arduion
    Serial.println(adc3 * 0.0625 / 1000, 4);
    //Serial.println(adc3);

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
    
    if (inChar == 's'){
     sdc();
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

  SPI.beginTransaction(SPISettings(66670000, MSBFIRST, SPI_MODE0));
  
  digitalWrite(CS_ADQ, LOW);
  chb[0] = SPI.transfer16(0b1101000000010000);
  SPI.transfer16(0b0000000000000000);
  digitalWrite(CS_ADQ, HIGH);
  SPI.endTransaction();

  digitalWrite(SLT, HIGH);
  delayMicroseconds(100);
  
  digitalWrite(CS_ADQ, LOW);
  chb[1] = SPI.transfer16(0b1101000000010000);
  SPI.transfer16(0b0000000000000000);
  digitalWrite(CS_ADQ, HIGH);
  SPI.endTransaction();

  digitalWrite(SLT, LOW);

  chv[0] = -(chb[0] * 24.576/65535) + 12.288;
  chv[1] = -(chb[1] * 24.576/65535) + 12.288;
  
}

void ReadChannelsOnce() {
  //digitalWrite(testpin, HIGH);
  //hold starts
  digitalWrite(HOLD, HIGH);
  ReadChannels();
  //Hold ends
  digitalWrite (HOLD, LOW);
  //digitalWrite (testpin, LOW);
  //reset the integration and a new integration process starts
  digitalWrite (RST, LOW);
  delayMicroseconds (resettime);
  digitalWrite (RST, HIGH);
  previousMillis = millis();
  //digitalWrite (testpin, HIGH);
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
  Wire.beginTransmission(0x48);
  Wire.write(0b00000001);
  Wire.write(0b01010000);
  Wire.write(0b11100010);
  Wire.endTransmission();
  Wire.beginTransmission(0x48);
  Wire.write(0b00000000);
  Wire.endTransmission();
  delay(5);
  Wire.requestFrom(0x48, 2);
  adc1 = (Wire.read() << 8 | Wire.read());
  PSV = adc1 * 0.1875 / 1000 * PSFC;
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
  while (millis() - previousMillis < integral){ 
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
  while (millis() - previousMillis < integral){ 
  }
  ReadChannelsOnce();
  
  while (!((chv[i] >= -0.005) && (chv[i] <= 0.005))){
   if (dcvchmax[i] - dcvchmin[i] == 1){
    break;
   }
   if (chv[i] < -0.005){ 
    dcvchmax[i] = dcvch[i];
   }
   if (chv[i] > 0.005){
    dcvchmin[i] = dcvch[i];
   }
   dcvch[i] = int((dcvchmin[i] + dcvchmax[i])/2);
   setvoltdc(i, dcvch[i]);
   while (millis() - previousMillis < integral){ 
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
   while (millis() - previousMillis < integral){ 
   }
   ReadChannelsOnce(); 
  }
 }
}
