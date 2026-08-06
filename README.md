<p align="center">
    <img src="assets/Logo.svg" width="500px"
</p>

<p align="center">
<a><img src=https://badgen.net/badge/Licence/CC%20BY-NC-SA%204.0></a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">

beakerDB ist eine Datenbank, die primär für Chemikalien entworfen wurde und für den Einsatz in kleinen bis mittelgroßen Gruppen gedacht ist, wie z.B. Arbeitskreise oder Schulen. 

Ein Feature von beakerDB ist die Unterstützung eines Barcodescanners. Mit einem Barcode versehene Chemikalien können so einfach gescannt und somit ihr Eintrag in der Datenbank angepasst werden.

## Installation

Die Datenbank kommt in Form einer Pythonanwendung, die einen lokalen Webserver unter `http://localhost:8050/` bereitstellt. 

### Anleitung
1. Die Anwendung benutzt Python 3.14. Python kannst du hier herunterladen: https://www.python.org/downloads/
2. Lade das Repository entweder manuell herunter oder klone es:
    ```shell
    git clone https://github.com/ProfessorOwl/beakerDB beakerDB
    cd beakerDB
    ```
3. Es ist sinnvoll, eine virtuelle Umgebung zu erstellen, damit die Python-Module nicht global installiert werden. *Achtung: Stelle sicher, dass du dich im Terminal im richten Ordner befindest!*
    - macOS/Linux:
        ```shell
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
        ```
    - Windows:
        ```shell
        python3 -m venv .venv
        .\.venv\Scripts\Activate.ps1
        pip install -r requirements.txt
        ```
4.  Der lokale Server kann nun gestartet werden mit 
    ```shell
    python layout.py
    ```
5. Anschließend kann die App im Browser unter `http://localhost:8050` geöffnet werden.

## Weitere Informationen

Im [Wiki](https://github.com/ProfessorOwl/beakerDB/wiki/Start) gibt es mehr Informationen zur Benutzung von beakerDB. 


