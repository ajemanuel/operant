const int buzzer = 12;     //buzzer to arduino pin 12
const int solenoid = 3;    // solenoid to arduino pin 3
const int lick = 7;        // lick input on pin 8
const int toneControl = 9; // toneControl input on pin 9
const int reward = 2;      //reward input on pin 2
const int squirt = 5;     //force reward with pin 0
const int abortIn = 4;    // abort input on pin 4
const int solenoidOpenDur = 28;

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
    //tone(buzzer, 4000, 100);
    digitalWrite(solenoid, HIGH);
    delay(solenoidOpenDur);
    digitalWrite(solenoid, LOW);
    delay(100); // wait at least 0.2 s (until next reward can be given)
  }

  if (digitalRead(abortIn) == HIGH && digitalRead(lick) == HIGH) {
    delay(5000); // abort trial by delaying and not allowing for tone or reward
  }

}
