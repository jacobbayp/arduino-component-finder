"""
ARDUINO KOMPONENT SØGNING SYSTEM - Python GUI

Dette program laver en GUI til at søge efter elektroniske komponenter
og vise deres placering ved at tænde tilhørende LED'er via Arduino.

Funktionalitet:
- Søg efter komponenter i realtid
- Tænd LED for valgt komponent (sender binær mask til Arduino)
- Tilføj/slet komponenter (gemmes i JSON fil)
- Test alle LED'er
- Automatisk Arduino forbindelse via USB Serial

Arkitektur:
- GUI: tkinter
- Data: komponenter.json (navn, skuffe, LED nummer)
- Kommunikation: PySerial (9600 baud)
- LED kontrol: Binær masks (1 << led_num)
"""

import tkinter as tk
from tkinter import messagebox
import serial
import serial.tools.list_ports
import json
import os
import time

class KomponentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Arduino Komponent Søgning System")
        self.root.geometry("800x550")
        self.root.minsize(700, 450)

        # Data og forbindelse
        self.data_file = "komponenter.json"
        self.components = []           # Alle komponenter fra JSON
        self.filtered_components = []  # Filtrerede resultater fra søgning
        self.arduino = None            # Serial forbindelse objekt
        self.connected = False         # Forbindelses status

        # Initialisér applikation
        self.load_components()
        self.create_gui()
        self.auto_connect()

    # ═══════════════════════════════════════════════════════════
    # GUI OPRETTELSE
    # ═══════════════════════════════════════════════════════════
    def create_gui(self):
        # ─────── Top bar: Arduino status og knapper ───────
        top = tk.Frame(self.root, bg="#2c3e50", height=40)
        top.pack(fill=tk.X)

        tk.Label(top, text="Arduino Status:", bg="#2c3e50",
                 fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=8)

        self.status_label = tk.Label(top, text="● Ikke forbundet", fg="#e74c3c",
                                     bg="#2c3e50", font=("Arial", 9, "bold"))
        self.status_label.pack(side=tk.LEFT)

        # Forbind/Afbryd knap (ændrer tekst dynamisk)
        self.connect_button = tk.Button(top, text="Forbind", command=self.toggle_connection,
                  bg="#3498db", fg="white", font=("Arial", 8))
        self.connect_button.pack(side=tk.LEFT, padx=8)
        
        tk.Button(top, text="Test LED'er", command=self.test_leds,
                  bg="#9b59b6", fg="white", font=("Arial", 8)).pack(side=tk.LEFT)

        # ─────── Søgefelt med real-time filtrering ───────
        search = tk.Frame(self.root, pady=10)
        search.pack(fill=tk.X)
        tk.Label(search, text="🔍 Søg:", font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=10)
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.on_search)  # Kald on_search() ved hver tast
        tk.Entry(search, textvariable=self.search_var, font=("Arial", 12), width=30).pack(side=tk.LEFT)
        tk.Button(search, text="Afslut søgning", command=self.clear_search, 
                  font=("Arial", 9)).pack(side=tk.LEFT, padx=10)

        # ─────── Resultat liste ───────
        results = tk.Frame(self.root)
        results.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        self.listbox = tk.Listbox(results, font=("Courier New", 11), 
                                   selectmode=tk.SINGLE, activestyle="dotbox")
        self.listbox.pack(fill=tk.BOTH, expand=True)
        
        # Event handlers for valg og tastatur navigation
        self.listbox.bind("<<ListboxSelect>>", self.on_select_component)
        self.listbox.bind("<Up>", self.on_arrow_key)
        self.listbox.bind("<Down>", self.on_arrow_key)
        self.listbox.focus_set()

        # ─────── Bundknapper: Vis alle, Tilføj, Slet ───────
        bottom = tk.Frame(self.root, pady=8)
        bottom.pack(fill=tk.X)
        tk.Button(bottom, text="📋 Vis alle", command=self.show_all,
                  bg="#3498db", fg="white", width=14, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom, text="➕ Tilføj", command=self.add_component_dialog,
                  bg="#2ecc71", fg="white", width=14, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom, text="❌ Slet", command=self.delete_component,
                  bg="#e74c3c", fg="white", width=14, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

    # ═══════════════════════════════════════════════════════════
    # DATA HÅNDTERING (JSON)
    # ═══════════════════════════════════════════════════════════
    def load_components(self):
        """Indlæs komponenter fra JSON fil"""
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as f:
                self.components = json.load(f)
        else:
            self.components = []
            self.save_components()

    def save_components(self):
        """Gem komponenter til JSON fil"""
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.components, f, indent=2)

    # ═══════════════════════════════════════════════════════════
    # ARDUINO KOMMUNIKATION
    # ═══════════════════════════════════════════════════════════
    def toggle_connection(self):
        """Skift mellem forbind og afbryd"""
        if self.connected:
            self.disconnect()
        else:
            self.auto_connect()
    
    def disconnect(self):
        """Afbryd forbindelse til Arduino"""
        if self.arduino:
            try:
                self.send_leds(0)  # Sluk alle LED'er før afbrydelse
                self.arduino.close()
            except:
                pass
        self.arduino = None
        self.connected = False
        self.status_label.config(text="● Ikke forbundet", fg="#e74c3c")
        self.connect_button.config(text="Forbind", bg="#3498db")
        print("Forbindelse afbrudt")
    
    def auto_connect(self):
        """Søg automatisk efter Arduino på USB-porte"""
        ports = list(serial.tools.list_ports.comports())
        
        for port in ports:
            # Filtrer USB/Arduino porte
            if "USB" in port.description or "Arduino" in port.description:
                try:
                    self.arduino = serial.Serial(port.device, 9600, timeout=1)
                    time.sleep(2)  # Vent på Arduino reset
                    
                    # Vent på "ARDUINO_READY" bekræftelse (max 5 sekunder)
                    start = time.time()
                    while time.time() - start < 5:
                        if self.arduino.in_waiting:
                            line = self.arduino.readline().decode(errors="ignore").strip()
                            if line == "ARDUINO_READY":
                                self.connected = True
                                self.status_label.config(text=f"● Forbundet ({port.device})", fg="#27ae60")
                                self.connect_button.config(text="Afbryd forbindelse", bg="#e67e22")
                                print(f"Forbundet til {port.device}")
                                return
                    self.arduino.close()
                except:
                    pass
        
        # Ingen Arduino fundet
        self.connected = False
        self.status_label.config(text="● Ikke forbundet", fg="#e74c3c")
        self.connect_button.config(text="Forbind", bg="#3498db")
        messagebox.showwarning("Forbindelse fejlet", "Kunne ikke finde Arduino på USB-porte")

    def send_leds(self, value):
        """Send LED kommando til Arduino
        
        Args:
            value: Binær mask (0-255) hvor hver bit = en LED
                   Eksempel: value=8 (0b00001000) tænder LED 4
        """
        if self.connected and self.arduino:
            try:
                command = f"LED:{value}\n"
                print(f"Sender: {command.strip()} (binær: {bin(value)})")
                self.arduino.write(command.encode())
                time.sleep(0.05)
            except Exception as e:
                print(f"Fejl ved sending: {e}")

    def test_leds(self):
        """Test alle LED'er ved at tænde dem individuelt"""
        if not self.connected:
            messagebox.showwarning("Fejl", "Arduino ikke forbundet")
            return
        
        if not self.components:
            messagebox.showinfo("Info", "Ingen komponenter tilføjet endnu")
            return
        
        print("Test starter - tester alle tilføjede komponenter")
        
        # Tænd hver LED individuelt (0.5 sek hver)
        for comp in self.components:
            led_num = comp["led"]
            led_mask = 1 << led_num  # Bit shift: 1<<0=1, 1<<1=2, 1<<2=4...
            print(f"Tester: {comp['name']} (LED {led_num+1})")
            self.send_leds(led_mask)
            time.sleep(0.5)
        
        # Sluk alle LED'er
        print("Slukker alle LED'er")
        self.send_leds(0)

    # ═══════════════════════════════════════════════════════════
    # SØGE LOGIK
    # ═══════════════════════════════════════════════════════════
    def on_search(self, *args):
        """Kaldes automatisk når bruger skriver i søgefeltet"""
        query = self.search_var.get().strip().upper()
        self.listbox.delete(0, tk.END)
        self.filtered_components = []

        if not query:
            self.send_leds(0)  # Sluk LED'er hvis søgning er tom
            return

        # Filtrer komponenter der matcher søgning
        for c in self.components:
            if query in c["name"].upper():
                self.filtered_components.append(c)
                drawer = c.get("drawer", "?")
                self.listbox.insert(tk.END, f"{c['name']:15} → {drawer}")

    def on_select_component(self, event):
        """Kaldes når bruger vælger en komponent fra listen"""
        selection = self.listbox.curselection()
        if not selection:
            self.send_leds(0)
            return
        
        index = selection[0]
        if index >= len(self.filtered_components):
            return
            
        component = self.filtered_components[index]
        led_num = component["led"]
        led_mask = 1 << led_num  # Konverter LED nummer til binær mask
        
        print(f"Valgt: {component['name']}, LED#{led_num+1}, Mask={led_mask}")
        self.send_leds(led_mask)

    def on_arrow_key(self, event):
        """Håndter piltast navigation i listen"""
        cur = self.listbox.curselection()
        if not cur:
            return
        
        idx = cur[0]
        if event.keysym == "Up":
            idx = max(0, idx - 1)
        elif event.keysym == "Down":
            idx = min(self.listbox.size() - 1, idx + 1)
        
        # Opdater selection og trigger LED ændring
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(idx)
        self.listbox.activate(idx)
        self.listbox.see(idx)
        self.on_select_component(None)

    def clear_search(self):
        """Nulstil søgning og sluk LED'er"""
        self.search_var.set("")
        self.listbox.delete(0, tk.END)
        self.filtered_components = []
        self.send_leds(0)

    def show_all(self):
        """Vis alle komponenter i listen"""
        self.listbox.delete(0, tk.END)
        self.filtered_components = self.components.copy()
        for c in self.components:
            drawer = c.get("drawer", "?")
            self.listbox.insert(tk.END, f"{c['name']:15} → {drawer} (LED {c['led']+1})")

    # ═══════════════════════════════════════════════════════════
    # TILFØJ KOMPONENT
    # ═══════════════════════════════════════════════════════════
    def add_component_dialog(self):
        """Åbn dialog til at tilføje ny komponent"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Tilføj komponent")
        dialog.geometry("300x200")
        dialog.grab_set()  # Blokér hovedvinduet mens dialog er åben

        tk.Label(dialog, text="Navn:").pack(pady=5)
        name_entry = tk.Entry(dialog, font=("Arial", 12))
        name_entry.pack(pady=5)

        tk.Label(dialog, text="Skuffe:").pack(pady=5)
        drawer_entry = tk.Entry(dialog, font=("Arial", 12))
        drawer_entry.pack(pady=5)

        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Fejl", "Navn må ikke være tomt")
                return
            drawer = drawer_entry.get().strip() or "?"

            # Find første ledige LED nummer (0-7)
            used_leds = [c["led"] for c in self.components]
            for led in range(8):
                if led not in used_leds:
                    new_led = led
                    break
            else:
                messagebox.showerror("Fejl", "Alle 8 LED'er er optaget")
                return

            # Gem ny komponent
            new_comp = {"name": name, "drawer": drawer, "led": new_led}
            self.components.append(new_comp)
            self.save_components()
            self.show_all()
            dialog.destroy()

        tk.Button(dialog, text="Tilføj", command=save, bg="#2ecc71", fg="white",
                  font=("Arial", 14, "bold"), width=15, height=2).pack(pady=10)

    # ═══════════════════════════════════════════════════════════
    # SLET KOMPONENT
    # ═══════════════════════════════════════════════════════════
    def delete_component(self):
        """Slet valgt komponent"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Fejl", "Vælg en komponent først")
            return
        
        index = selection[0]
        if index >= len(self.filtered_components):
            return
        
        component = self.filtered_components[index]
        if messagebox.askyesno("Bekræft", f"Slet {component['name']}?"):
            self.components.remove(component)
            self.save_components()
            self.show_all()
            self.send_leds(0)  # Sluk LED efter sletning

# ═══════════════════════════════════════════════════════════
# PROGRAM START
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app = KomponentApp(root)
    root.mainloop()