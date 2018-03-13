// Include the ESP8266 WiFi library. (Works a lot like the
// Arduino WiFi library.)
#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>

#include <Wire.h>


//////////////////////
// WiFi Definitions //
//////////////////////
const char WiFiSSID[] = "karantza";
const char WiFiPSK[] = "science!";

/////////////////////
// Pin Definitions //
/////////////////////
const int LED_PIN = 5; // Thing's onboard, green LED

const int ANALOG_PIN = A0; // The only analog pin on the Thing
const float POLL_INTERVAL = 60; // in seconds


const char hostname[] = "192.168.1.215";
const int hostport = 80;

float degreesC = 0;

WiFiClient client;

void setup() 
{
  initHardware(); // Setup input/output I/O pins
  connectWiFi(); // Connect to WiFi
  digitalWrite(LED_PIN, LOW); // LED on to indicate connect success
}

void loop() 
{
  gatherData();
  
  Serial.println("Posting data");
  postData();

  delay((int)(1000.f * POLL_INTERVAL));
}

void connectWiFi()
{
  byte ledStatus = LOW;
  Serial.println();
  Serial.println("Connecting to: " + String(WiFiSSID));
  // Set WiFi mode to station (as opposed to AP or AP_STA)
  WiFi.mode(WIFI_STA);

  // WiFI.begin([ssid], [passkey]) initiates a WiFI connection
  // to the stated [ssid], using the [passkey] as a WPA, WPA2,
  // or WEP passphrase.
  WiFi.begin(WiFiSSID, WiFiPSK);

  // Use the WiFi.status() function to check if the ESP8266
  // is connected to a WiFi network.
  while (WiFi.status() != WL_CONNECTED)
  {
    // Blink the LED
    digitalWrite(LED_PIN, ledStatus); // Write LED high/low
    ledStatus = (ledStatus == HIGH) ? LOW : HIGH;

    // Delays allow the ESP8266 to perform critical tasks
    // defined outside of the sketch. These tasks include
    // setting up, and maintaining, a WiFi connection.
    delay(100);
    // Potentially infinite loops are generally dangerous.
    // Add delays -- allowing the processor to perform other
    // tasks -- wherever possible.
  }
  Serial.println("WiFi connected");  
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void initHardware()
{
  Serial.begin(9600);
  
  pinMode(LED_PIN, OUTPUT); // Set LED as output
  digitalWrite(LED_PIN, HIGH); // LED off

  pinMode(ANALOG_PIN, INPUT);

  Wire.begin();

}

void gatherData()
{

  float voltage, degreesF;

  // First we'll measure the voltage at the analog pin. Normally
  // we'd use analogRead(), which returns a number from 0 to 1023.
  // Here we've written a function (further down) called
  // getVoltage() that returns the true voltage (0 to 5 Volts)
  // present on an analog input pin.

  float total = 0;

  Serial.print("measuring...");
  for (int i = 0; i < 100; i++) {
    total += (float)analogRead(ANALOG_PIN);
    digitalWrite(LED_PIN, i % 2);
    delay(50);
  }
  digitalWrite(LED_PIN, HIGH);

  voltage = getVoltage(total * .01);

  // .750 v @ 25C, .01v/C = 0.5v @ 0C
  degreesC = (voltage - 0.5) * 100.0;
  
  degreesF = degreesC * (9.0/5.0) + 32.0;
 
  Serial.print("  deg C: ");
  Serial.print(degreesC);

  Serial.println();
}

float getVoltage(float value)
{
 // 0-1023 = 0-1 because it's a 1v max
 
  return (value / 1023.0) + 0.04;
}

int postData()
{
  // LED turns on when we enter, it'll go off when we 
  // successfully post.
  digitalWrite(LED_PIN, LOW);


  if (client.connect(hostname, hostport)) {
    // we are connected to the host!
    
    Serial.println("[Sending a request]");
    
    client.print(String("GET /set?temp=") + String(degreesC) + " HTTP/1.1\r\n" +
             "Host: " + hostname + "\r\n" +
             "Connection: close\r\n" +
             "\r\n"
            );
            
    Serial.println("[Response:]");

    while (client.connected()) {
      if (client.available()) {
        String line = client.readStringUntil('\n');
        Serial.println(line);
      }
    }
    
    client.stop();
    Serial.println("\n[Disconnected]");

  } else {
    // connection failure
    Serial.print("connection to ");
    Serial.print(hostname);
    Serial.println(" failed.");
  }


  // Before we exit, turn the LED off.
  digitalWrite(LED_PIN, HIGH);

  return 1; // Return success
}




