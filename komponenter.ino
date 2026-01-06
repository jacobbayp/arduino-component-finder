/*
 * ARDUINO KOMPONENT SØGNING SYSTEM
 * 
 * Dette program modtager kommandoer via USB Serial fra en Python GUI
 * og styrer LED'er gennem et 74HC595 shift register via SPI.
 * 
 * Funktionalitet:
 * - Modtager "LED:X" kommandoer hvor X er en binær mask (0-255)
 * - Hver bit i masken repræsenterer en LED (bit 0 = LED 1, bit 1 = LED 2, osv.)
 * - Kommunikerer med 74HC595 via hardware SPI (SCK + MOSI) og manuel LATCH kontrol
 * - Understøtter test-funktion der cykler gennem alle LED'er
 * 
 * Hardware: Arduino MEGA 2560, 74HC595 shift register, LED'er med 220Ω modstande
 */

#include <SPI.h>

#define LATCH_PIN 53  // Pin 53 styrer 74HC595's RCLK (opdaterer LED outputs)

void setup() {
  Serial.begin(9600);
  Serial.setTimeout(100);

  // Konfigurer SPI hardware
  pinMode(LATCH_PIN, OUTPUT);
  SPI.begin();                             // Initialisér SPI (Pin 50-52 på MEGA)
  SPI.setBitOrder(MSBFIRST);               // Most Significant Bit først
  SPI.setClockDivider(SPI_CLOCK_DIV16);    // Clock hastighed: 1MHz

  // Nulstil shift registeret (sluk alle LED'er ved opstart)
  digitalWrite(LATCH_PIN, LOW);
  SPI.transfer(0x00);
  digitalWrite(LATCH_PIN, HIGH);
  delay(100);

  // Send bekræftelse til Python
  Serial.println("ARDUINO_READY");
}

void loop() {
  // Lyt efter kommandoer fra Python via Serial
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toUpperCase();

    // Håndter "TEST" kommando
    if (cmd.equals("TEST")) {
      testAllLEDs();
    }
    // Håndter "LED:X" kommando (X = binær mask 0-255)
    // Eksempel: "LED:8" = 0b00001000 = tænd LED 4
    else if (cmd.startsWith("LED:")) {
      int value = cmd.substring(4).toInt();  // Ekstrahér tal efter "LED:"
      if (value >= 0 && value <= 255) {
        writeSPIShiftRegister((byte)value);
      }
    }
  }
}

// Sender en byte til 74HC595 via SPI
// LATCH LOW → Send data → LATCH HIGH (opdaterer LED'er)
void writeSPIShiftRegister(byte data) {
  digitalWrite(LATCH_PIN, LOW);   // Forbered modtagelse
  SPI.transfer(data);             // Send 8 bits via hardware SPI
  digitalWrite(LATCH_PIN, HIGH);  // Kopiér til outputs (LED'er opdateres nu)
  delay(1);

  Serial.print("Mask skrevet via SPI: ");
  Serial.println(data, BIN);
}

// Test-sekvens: Tænder LED'er 0-4 individuelt, derefter alle sammen
void testAllLEDs() {
  Serial.println("TEST starter");
  
  // Tænd hver LED individuelt
  for (int i = 0; i < 5; i++) {
    byte mask = 1 << i;  // Bit shift: 0b00000001, 0b00000010, 0b00000100...
    writeSPIShiftRegister(mask);
    delay(500);
  }
  
  writeSPIShiftRegister(0x1F);  // 0b00011111 = Tænd LED 0-4 samtidig
  delay(1000);
  writeSPIShiftRegister(0);     // Sluk alle LED'er
}