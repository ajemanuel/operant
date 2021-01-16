const int buzzer = 2;     //  
const int solenoid = 5  ;    //  inferred from rewardValvePin
const int lick = 10;        // inferred from lickSensorPin
const int toneControl = 3; // 
const int reward = 13;      // inferred from rewardActivePin
const int punish = 9;    // from
const int squirt = 4;     // NEED TO INSTALL
const int abortIn = 7;   // NEED TO DEFINE/INSTALL
const int solenoidOpenDur = 25;

void setup() {

  pinMode(buzzer, OUTPUT); // Set buzzer - pin 12 as an output
  pinMode(lick, INPUT); // Set lick - pin 8 as an input
  pinMode(toneControl, INPUT); // Set toneControl - pin 9 as an input
  pinMode(reward, INPUT); // Set reward - pin 2 as an input
}

void loop() {
  if (digitalRead(toneControl) == HIGH) {
    tone(buzzer, 1500, 200);
  }


  if (digitalRead(lick) == HIGH && digitalRead(reward) == HIGH) {
    digitalWrite(solenoid, HIGH);
    delay(solenoidOpenDur);
    digitalWrite(solenoid, LOW);
    delay(3000); // wait at least 3 s (until next trial begins)
  }

  if (digitalRead(squirt) == HIGH) {
    tone(buzzer, 4000, 100);
    digitalWrite(solenoid, HIGH);
    delay(solenoidOpenDur);
    digitalWrite(solenoid, LOW);
    delay(100); // wait at least 0.2 s (until next reward can be given)
  }

  if (digitalRead(abortIn) == HIGH && digitalRead(lick) == HIGH) {
    delay(5000); // abort trial by delaying and not allowing for tone or reward
  }

}