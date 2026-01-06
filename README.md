# Arduino Komponent Søgning System

Find komponenter med Arduino og LED'er - søg på din computer og den rigtige LED lyser op!

## 📦 Hvad er dette?

Et system der hjælper med at finde elektroniske komponenter i skuffer. Når du søger efter en komponent i programmet, tænder den tilhørende LED automatisk for at vise hvor komponenten ligger.

## 🔧 Komponenter

- Arduino MEGA 2560
- 74HC595 Shift Register
- 8x LED'er
- 8x 220Ω modstande
- Breadboard og kabler

## 📁 Filer

- `komponenter.ino` - Arduino kode (modtager kommandoer og styrer LED'er via SPI)
- `komponenter.py` - Python GUI (søgning og komponent administration)
- `komponenter.json` - Database med komponenter (navn, skuffe, LED nummer)

## 🚀 Opsætning

### Hardware
1. Tilslut 74HC595 til Arduino MEGA 2560:
   - **Pin 51 (MOSI)** → **DS (pin 14)** - Data input
   - **Pin 52 (SCK)** → **SHCP (pin 11)** - Shift clock
   - **Pin 53** → **STCP (pin 12)** - Latch clock
   - **5V** → **VCC (pin 16)**
   - **GND** → **GND (pin 8)**
   - **GND** → **OE (pin 13)** - Output enable (altid aktiv)
2. Tilslut LED'er til 74HC595 outputs:
   - Q0-Q7 (pin 15, 1-7) → 220Ω modstand → LED anode
   - Alle LED katoder → GND

### Software
1. Upload `komponenter.ino` til Arduino
2. Installér Python biblioteker:
```bash
   pip install pyserial
```
3. Kør GUI'en:
```bash
   python komponenter.py
```

## 💡 Brug

1. Programmet finder automatisk Arduino på USB
2. Søg efter komponenter i søgefeltet
3. Vælg en komponent → LED'en lyser op
4. Tilføj nye komponenter med ➕ knappen
5. Test alle LED'er med "Test LED'er" knappen

## 📊 Diagrammer

- [Kredsløbsdiagram (PDF)](images/diagram.pdf)
- [Flowchart (PDF)](images/flowchart.pdf)

## 🛠️ Teknisk info

- **Kommunikation:** USB Serial (9600 baud)
- **LED kontrol:** Binær masks (1 << led_num)
- **Max LED'er:** 8 (kan udvides med flere shift registers)
- **Data format:** JSON fil med komponenter
