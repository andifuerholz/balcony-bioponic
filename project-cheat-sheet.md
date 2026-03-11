# Arduino IoT Cloud × MicroPython — Cheat Sheet

## 1) Purpose & Prereqs
- Ziel: Ein Arduino‑Board (z. B. Nano ESP32) mit MicroPython an die Arduino IoT Cloud anbinden, Variablen synchronisieren und via Callbacks auf Änderungen reagieren.
- Voraussetzung: MicroPython ist sauber installiert und das Board kann über einen Editor (Arduino Lab / mpremote) angesprochen werden.

---

## 2) Cloud Setup (Thing, Device, Dashboard)
1. In der Arduino Cloud ein **Thing** anlegen.
2. Ein **Device** hinzufügen (manuelles Gerät) → **Device ID** und **Secret Key** sicher speichern.
3. **Cloud‑Variablen** anlegen (Bezeichnungen müssen exakt zu deinem Code passen).
4. **Dashboard** erstellen, Widgets hinzufügen und mit den Variablen verknüpfen.

---

## 3) Files on the Board
- **`secrets.py`** enthält WLAN‑Daten sowie Device‑ID und Cloud‑Passwort.  
- **`boot.py`** (optional): frühe Initialisierungen wie WLAN‑Verbindung.  
- **`main.py`**: Hauptprogramm mit State Machine, Sensor‑Loops und Cloud‑Client.  
- Bibliotheken in den Ordner **`/lib`** legen.

---

## 4) Installation der Cloud‑Library
- Mit `mpremote` auf das Board zugreifen und die Arduino‑Cloud‑Library per `mip install` aufspielen.

---

## 5) WLAN-Verbindung (Essentials)
- WLAN über `network.WLAN(STA_IF)` aktivieren und verbinden.
- Retry‑Schleife mit kurzen Wartezeiten einbauen.
- Logging nutzen, um den Verbindungsstatus auszugeben.

---

## 6) Cloud Client Basics
- **Client erzeugen:**  
  `ArduinoCloudClient(device_id=DEVICE_ID, username=DEVICE_ID, password=CLOUD_PASSWORD)`
- **Variablen registrieren:**  
  `client.register("var_name", value=None, on_write=callback)`
- **Client starten:**  
  - **Async (empfohlen):** `client.start()`  
  - **Sync:** `client.start()` plus regelmäßige `client.update()`‑Aufrufe im Loop.

---

## 7) Async vs. Sync (Wann benutzen?)
- **Async:**  
  Nicht‑blockierend; ideal, wenn Sensoren gelesen, Pumpen/Relais geschaltet und Cloud‑Kommunikation parallel laufen sollen.  
  → Für dein Bewässerungssystem klar die beste Wahl.
- **Sync:**  
  Einfacher, aber blockierend bei Netzwerk‑IO; nur sinnvoll für sehr simple Loops.

---

## 8) Callbacks (Pattern)
- Ein `on_write(client, value)`‑Callback reagiert auf Änderungen aus dem Dashboard.
- Innerhalb des Callbacks können:
  - lokale Aktoren geschaltet werden (z. B. LED, Relais, Pumpe),
  - andere Cloud‑Variablen aktualisiert werden (`client["led"] = value`).

---

## 9) Dashboard & Advanced Variable Types
- Widgets (LED, Switch, Slider, Numeric, etc.) mit Cloud‑Variablen verbinden.
- Für komplexere Variablen (z. B. Farbwerte) passende Klassen importieren und registrieren.
- Callback erhält dann ein Objekt mit mehreren Feldern (z. B. `swi`, `hue`, `sat`, `bri`).

---

## 10) Troubleshooting Quick List
- MicroPython‑Version korrekt installiert?
- `secrets.py` vollständig und korrekt?
- Device dem Thing zugewiesen?
- Variablennamen im Dashboard und Code identisch?
- WLAN‑Signal ausreichend?
- Falls nötig: Logging-Level auf DEBUG setzen.

---

## 11) Project Notes (Bioponics)
- Async‑Client nutzen: erleichtert paralleles Auslesen von Außen‑ und Wassertemperatur sowie das zeitabhängige Schalten der Bewässerung.
- Mögliche Variablen:
  - `AirTemp`
  - `AirTempAvg`
  - `WaterTemp`
  - `TankLevel`
  - `ManualOverride`
  - `Circuit1Schedule`
  - `Circuit2Schedule`
  - `PumpActive`
  - `ValveState`
- State Machine in `main.py`:  
  Temperatur → Bewässerungslogik → Pumpen/Relais schalten → Rückmeldung in die Cloud.

---

## 12) Minimal Checklist
1. MicroPython installiert, Board erreichbar.
2. Thing, Device und Variablen in der Cloud angelegt.
3. `secrets.py` mit WLAN + Cloud-Credentials auf dem Board.
4. Cloud‑Library via `mpremote` installiert.
5. In `main.py`: WLAN verbinden, Client erzeugen, Variablen registrieren, `client.start()`.
6. Dashboard öffnen und Funktionen testen.
