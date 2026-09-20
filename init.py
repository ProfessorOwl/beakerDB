from dash import Dash

import json
from pathlib import Path
import waitress
import argparse

from callbacks import get_callbacks
import functions
from layout import MantineProvider
from default_values import VERSION, LANG

# Command Line Interface
parser = argparse.ArgumentParser(
    "beakerDB", "Startet eine Chemikaliendatenbank als lokalen Server"
)
parser.add_argument(
    "-v",
    "--version",
    action="version",
    version=VERSION,
    help="Zeige die Versionsnummer von beakerDB",
)
parser.add_argument(
    "-d", "--debug", action="store_true", help="Starte den Server im Debug-Modus."
)
parser.add_argument(
    "--host",
    default="127.0.0.1",
    help="Definiere die IP-Adresse, auf der der Server gehostet wird. (Standard: %(default)s)",
)
parser.add_argument(
    "-p",
    "--port",
    default=8050,
    help="Definiere den Port des Servers. (Standard %(default)i)",
)
args = parser.parse_args()

# Definiere den Server der Datenbank
app = Dash(__name__)
app.__init__(prevent_initial_callbacks=True)
app.title = "beakerDB"
app.layout = MantineProvider
functions.init_app(LANG)

if __name__ == "__main__":

    get_callbacks(app)
    if args.debug:
        app.run(
            debug=args.debug, host=args.host, port=args.port, dev_tools_hot_reload=False
        )
    else:
        print(
            f"Flask launched on http://{args.host}:{args.port}{" or http://localhost:"+str(args.port) if args.host == "127.0.0.1" else ""}. Debug mode is {"on" if args.debug else "off"}."
        )
        waitress.serve(app.server, host=args.host, port=args.port, threads=8)
