<p align="center">
    <img src="assets/Logo.svg" width="500px"
</p>

<p align="center">
<a><img src=https://badgen.net/badge/Licence/CC%20BY-NC-SA%204.0></a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">

*beakerDB* is a database for chemicals for use in small to medium-sized groups, for example in scientific groups or schools. It uses *sqlite* as its database backend.

*beakerDB* currently has the following features that enhance it beyond using a plain excel table:
- Quickly catalogue chemicals using a **barcode scanner** for searching and creating new entries
- Run a **server** to give your group up-to-date information about chemicals that you have stored
- Automatically set the **date of inspection** when changing or creating entries
- Make interval based **automatic backups** of the database
- **Archive** chemicals that where sorted out or are empty, to keep a well documented history of all chemicals
- Connect chemicals with a **safety sheet** from [GESTIS](https://gestis-database.dguv.de/)
- Manage **masterdata** to keep your suppliers, manufacturers, rooms and buildings in order

## Installation

*beakerDB* is a python application that runs a local webserver under `http://localhost:8050/` by default.

### Anleitung
1. The application uses Python 3.14. You can download Python here: https://www.python.org/downloads/.
2. Download the [latest version](https://github.com/ProfessorOwl/beakerDB/releases/latest) of *beakerDB*  and unpack it somewhere.
3. You should create a virtual environment for Python, so that the Python modules won't be installed globally. *Warning: Make sure that you are in the installation folder of the app containing init.py.*
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
4.  The local server can then be started by running
    ```bash
    python init.py
    ```
    The app supports **command line arguments**. With them, you can quickly change the port or IP adress of the app. For a quick overview run
    ```bash
    python init.py -h
    ```
5. You can access the server under `http://localhost:8050`.
