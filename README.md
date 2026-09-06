<p align="center">
    <img src="assets/Logo.svg" width="500px"
</p>

<p align="center">
<a><img src=https://badgen.net/badge/Licence/CC%20BY-NC-SA%204.0></a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">

*beakerDB* ist eine Chemikaliendatenbank, die für den Einsatz in kleinen bis mittelgroßen Gruppen gedacht ist, wie z.B. Arbeitskreise oder Schulen. 

*beakerDB* zeichnet sich durch folgende Eigenschaften aus:
- Unterstützung eines **Barcodescanners**, um Chemikalien schnell zu katalogisieren
- Automatisches Aktualisieren des **Prüfdatums** beim Erstellen/Ändern von Einträgen
- Zeitbasierte **Backups** der Datenbank
- **Archiv** für aussortierte/verworfene Chemikalien, für eine nachvollziehbare Chemikaliengeschichte
- Möglichkeit, Chemikalien mit ihrem **GESTIS**-Eintrag zu verbinden
- Anlegen **fester Stammdaten**, um Ordnung bei verschiedenen Lieferanten, Herstellen, Räumen und Gebäuden zu behalten
- Lokales Datenbankmanagement mit **SQLite**

## Installation

Die Datenbank kommt in Form einer Pythonanwendung, die einen lokalen Webserver unter `http://localhost:8050/` bereitstellt. 

### Anleitung
1. Die Anwendung benutzt Python 3.14. Python kannst du hier herunterladen: https://www.python.org/downloads/
2. Lade das Repository entweder manuell herunter oder klone es:
    ```bash
    git clone https://github.com/ProfessorOwl/beakerDB beakerDB
    cd beakerDB
    ```
3. Es ist sinnvoll, eine virtuelle Umgebung zu erstellen, damit die Python-Module nicht global installiert werden. *Achtung: Stelle sicher, dass du dich im Terminal im richten Ordner befindest!*
    - macOS/Linux:
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
        ```
    - Windows:
        ```bash
        python3 -m venv .venv
        .\.venv\Scripts\Activate.ps1
        pip install -r requirements.txt
        ```
4.  Der lokale Server kann nun gestartet werden mit 
    ```bash
    python layout.py
    ```
    Es können mehrere **Startoptionen** hinzugefügt werden, um z.B. die IP-Adresse oder den Port der Datenbank anzupassen. Für eine Übersicht einfach 
    ```bash
    python layout.py -h
    ```
     eingeben.
5. Anschließend kann die App im Browser unter `http://localhost:8050` geöffnet werden.
