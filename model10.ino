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
#define RAN_1 7 
#define RAN_2 A4
#define RAN_3 A1
#define RAN_4 A0
#define SHD_REF 9
//#define CS_POT 10
#define PSFC 16.39658
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
unsigned long integraltimemicros = 700;
int resettimemicros = 10;

bool printtoconsole = false;

unsigned int countvolt = 1;

unsigned long previousmillis = 0;
unsigned long initialintegralmicros = 0;
unsigned long integralmicros = 0;
unsigned long startmicros = 0;
unsigned long count = 0;

//dac value in counts from 0 to 65535
int daclow;
int dachigh;
int dacnow = 1;

float setvolt = 56.56;
float PSV;

float temp = 27;
unsigned int tempbytes;

byte arraytosend[22];


//darkcurrents
unsigned int dcvch[] = {5000, 3000};
unsigned int dcvchmax[] = {6553, 65535};
unsigned int dcvchmin[] = {0, 0};

unsigned int chb[] = {0, 0};
float chv[] = {0.0, 0.0};


void setup() {

  //arraytosend[22] = 126;
  //arraytosend[23] = 126;
  
  
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
  //pinMode(CS_POT, OUTPUT);
  pinMode(testpin, OUTPUT);

  digitalWrite(CS_ADQ0, HIGH);
  digitalWrite(RST, HIGH);
  digitalWrite(HOLD, LOW);
  digitalWrite(CS_ADQ1, HIGH);
  digitalWrite(SHD_PS, LOW);
  digitalWrite(SHD_REF, LOW);
  digitalWrite(RAN_1, LOW);
  digitalWrite(RAN_2, LOW);
  digitalWrite(RAN_3, HIGH);
  digitalWrite(RAN_4, LOW);
  //digitalWrite(CS_POT, HIGH);
  

  Serial.begin(115200);
  Wire.begin();
  SPI.begin();

  //Turn on the reference of the dark current DAC
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

  //Set the PS DAC to devide by 2 and multiply by 1
  //the internal reference of 2.5 V to get 1.25 V
  Wire.beginTransmission(0x4b);
  Wire.write(0x4); //comand byte Gain register
  Wire.write(0x1); //devide by 2
  Wire.write(0x0); //multiply by 1
  Wire.endTransmission();

  //digitalWrite(SHD_REF, HIGH);
  
  //Then wait 2 seconds and turn on the Power Suplly
  delay(2000);
  digitalWrite (SHD_PS, LOW);

  
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
  setPSDAC(55300);

  adc.setConvRate(ADS1115_860_SPS);
  adc.setVoltageRange_mV(ADS1115_RANGE_6144);
  
}


void loop() {
  

  if (micros() - initialintegralmicros >= integraltimemicros){
    ReadChannelsOnceandsend();
    switch(countvolt){
      case 1:
        adc.setCompareChannels(ADS1115_COMP_0_GND);
        adc.startSingleMeasurement();
        break;
       case 3:
        adc0 = adc.getRawResult();
        arraytosend[10] = adc0 >> 8;
        arraytosend[11] = adc0 & 0xFF;
        //adc0V = adc.getResult_V();
        break;
       case 5:
        adc.setCompareChannels(ADS1115_COMP_1_GND);
        adc.startSingleMeasurement();
        break;
       case 7:
        adc1 = adc.getRawResult();
        arraytosend[12] = adc1 >> 8;
        arraytosend[13] = adc1 & 0xFF;
        //adc1V = adc.getResult_V();
        break;
       case 9:
        adc.setCompareChannels(ADS1115_COMP_2_GND);
        adc.startSingleMeasurement();
        break;
       case 11:
        adc2 = adc.getRawResult();
        arraytosend[14] = adc2 >> 8;
        arraytosend[15] = adc2 & 0xFF;
        //adc2V = adc.getResult_V();
        break;
       case 13:
        adc.setVoltageRange_mV(ADS1115_RANGE_2048);
        break;
       case 15:
        adc.setCompareChannels(ADS1115_COMP_3_GND);
        adc.startSingleMeasurement();
        break;
       case 17:
        adc3 = adc.getRawResult();
        arraytosend[16] = adc3 >> 8;
        arraytosend[17] = adc3 & 0xFF;
        //adc3V = adc.getResult_V();
        break;
       case 19:
        adc.setVoltageRange_mV(ADS1115_RANGE_6144);
        break;
       case 21:
        temp = tempsensor.readTempC();
        tempbytes = tempsensor.read16(0x05);
        arraytosend[8] = tempbytes >> 8;
        arraytosend[9] = tempbytes & 0xFF;
        break;
       case 22:
        countvolt = 0;
        break;
       
    }
    countvolt += 1;
  }

  //PROTOCOLO DE COMUNICACION
  if (Serial.available() > 0) {
    char inChar = (char)Serial.read();
    
    //REGULATE POWER SUPPLY    
    if (inChar == 'r'){
      String PSs = Serial.readStringUntil(',');
      char comma = Serial.read(); //discard comma at the end
      Serial.println(PSs.toFloat(), 2);
      setvolt = PSs.toFloat();
      regulatePS();
    }

    //SELECT INTEGRATOR CAPACITOR RANGE
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

    //PRINT TO CONSOLE
    if (inChar == 'h'){
      printtoconsole = true;
    }

    if (inChar == 'b'){
      printtoconsole = false;
    }

    //SUBTRACT DARK CURRENT
    if (inChar == 's'){
     Serial.println("s preseed");
     delay(1000);
     sdc();
    }

    //SET DAC MANUALLY use int from 0 to 65535
    if (inChar == 'p'){
      String stringsetpotcounts = Serial.readStringUntil(',');
      char comma = Serial.read();
      int setdaccounts = stringsetpotcounts.toInt();
      Serial.print("Set DAC to ");
      Serial.println(setdaccounts);
      delay(1000);
      setPSDAC(setdaccounts);
    }

    //RESTART MICROSECONDS CLOCK
    if (inChar == 't'){
      startmicros = micros();
      count = 0;
    }

    //SET DARK CURRENT MANUALLY
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

     //TURN ON OFF POWER SUPPLY
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
  //digitalWrite(testpin,HIGH);
  //digitalWrite(testpin, HIGH);
  SPI.beginTransaction(SPISettings(66670000, MSBFIRST, SPI_MODE0));
  digitalWrite(CS_ADQ0, LOW);
  chb[0] = SPI.transfer16(0b1101000000010000);
  SPI.transfer16(0b0000000000000000);
  digitalWrite(CS_ADQ0, HIGH);
  //digitalWrite(testpin, LOW);
  SPI.endTransaction();
  //digitalWrite(testpin, LOW);
  
  SPI.beginTransaction(SPISettings(66670000, MSBFIRST, SPI_MODE0));
  digitalWrite(CS_ADQ1, LOW);
  chb[1] = SPI.transfer16(0b1101000000010000);
  SPI.transfer16(0b0000000000000000);
  digitalWrite(CS_ADQ1, HIGH);
  SPI.endTransaction();

  arraytosend[18] = chb[0] >> 8;
  arraytosend[19] = chb[0] & 0xFF;
  arraytosend[20] = chb[1] >> 8;
  arraytosend[21] = chb[1] & 0xFF;

  //chv[0] = -(chb[0] * 24.576/65535) + 12.288;
  //chv[1] = -(chb[1] * 24.576/65535) + 12.288;
  
}

void ReadChannelsOnceandsend(){
   //digitalWrite(testpin, HIGH);
   ReadChannelsOnce();

    //digitalWrite(testpin, HIGH);
    arraytosend[0] = (count >> 24) & 0xFF;
    arraytosend[1] = (count >> 16) & 0xFF;
    arraytosend[2] = (count >> 8) & 0xFF;
    arraytosend[3] = count & 0xFF;

    unsigned long timesincestart = micros() - startmicros;
    arraytosend[4] = (timesincestart >> 24) & (0xFF);
    arraytosend[5] = (timesincestart >> 16) & (0xFF);
    arraytosend[6] = (timesincestart >> 8) & (0xFF);
    arraytosend[7] = timesincestart & 0xFF;

    if (printtoconsole){
      Serial.print(count);
      Serial.print(",");
      Serial.print(timesincestart);
      Serial.print(",");
      Serial.print(temp, 4);
      Serial.print(",");
      
      //adc0 5V
      Serial.print(adc0*0.1875/1000, 4);
      Serial.print(",");
      //adc1 PS
      Serial.print(adc1*0.1875*16.39658/1000, 4);
      Serial.print(",");
      //adc2 -15
      Serial.print(adc2*0.1875*-4.6887/1000, 4);
      Serial.print(",");
      //adc3 ref 1.25V
      Serial.print(adc3*0.0625/1000, 4);

      Serial.print(",");
      Serial.print(chb[0]*-24.576/65535 + 12.288, 4);
      Serial.print(",");
      Serial.println(chb[1]*-24.576/65535 + 12.288, 4);
    }
    else{
      Serial.write(arraytosend, 22);
    }

    
    //digitalWrite(testpin, LOW);
    count = count + 1;
}

void ReadChannelsOnce() {
  
  digitalWrite(testpin, HIGH);
  //hold starts
  digitalWrite(HOLD, HIGH);
  delayMicroseconds(10);
  ReadChannels();
  //digitalWrite (testpin, LOW);
  //reset the integration and a new integration process starts
  digitalWrite (RST, LOW);
  delayMicroseconds (resettimemicros);
  digitalWrite (RST, HIGH);
  delayMicroseconds(10);
  //Hold ends
  //digitalWrite(testpin,HIGH);
  digitalWrite (HOLD, LOW);
  digitalWrite(testpin,LOW);
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
  dacnow = 320;
  setPSDAC(dacnow);
  //delay (1000);
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
      dacnow = dacnow - 1;
    }
    //voltage is too low
    else if (PSV < (setvolt - 0.008)){
      //potlow = potnow;
      dacnow = dacnow + 1;
    }
    //potnow = int((potlow + pothigh) / 2);
    setPSDAC(dacnow);
    readPS();
    Serial.print("setvolt,");
    Serial.print(setvolt, 2);
    //Serial.print(",pothigh,");
    //Serial.print(pothigh);
    Serial.print(",dacnow,");
    Serial.print(dacnow);
    //Serial.print(",daclow,");
    //Serial.print(daclow);
    Serial.print(",PS,");
    Serial.println(PSV, 4);
    //digitalWrite (ledpin, HIGH);

  }
}

void readPS(){
  adc.setVoltageRange_mV(ADS1115_RANGE_6144);
  adc.setCompareChannels(ADS1115_COMP_1_GND);
  adc.startSingleMeasurement();
  delay(1000);
  PSV = adc.getResult_V() * PSFC;
}

void setPSDAC(int x){
  Wire.beginTransmission(0x4b);
  Wire.write(0x8); //comand byte DAC DATA
  Wire.write(x >> 8);
  Wire.write(x & 0xFF);
  Wire.endTransmission();
}


//function to substract dark current
void sdc(){
  Serial.println("Subtract Dark Current initiated");
  unsigned int dccount = 65534;
  setvoltdc(0, dccount);
  delay(1);
  while (micros() - initialintegralmicros < integralmicros){}
  ReadChannelsOnce();
  Serial.print(0);
  Serial.print(",dccount,");
  Serial.print(dccount);
  Serial.print(",chb,");
  Serial.println(chb[0]);
  while (micros() - initialintegralmicros < integralmicros){}
  ReadChannelsOnce();
  while (chb[0] < 62000){
    dccount = dccount - 1;
    setvoltdc(0, dccount);
    while (micros() - initialintegralmicros < integralmicros){}
    ReadChannelsOnce();
    Serial.print(0);
    Serial.print(",dccount,");
    Serial.print(dccount);
    Serial.print(",chb,");
    Serial.println(chb[0]);
    while (micros() - initialintegralmicros < integralmicros){}
    ReadChannelsOnce();
  }
  
}


void sdcold(){
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
  
  while (!((chv[i] <= -10.0005) && (chv[i] >= -9.9995))){
   if (dcvchmax[i] - dcvchmin[i] == 1){
    break;
   }
   if (chv[i] < -10.0005){ 
    dcvchmax[i] = dcvch[i];
   }
   if (chv[i] > -9.9995){
    dcvchmin[i] = dcvch[i];
   }
   dcvch[i] = int((dcvchmin[i] + dcvchmax[i])/2);
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
  }
 }
}
