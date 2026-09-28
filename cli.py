import argparse
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
    help="Show the version of beakerDB",
)
parser.add_argument(
    "-d", "--debug", action="store_true", help="Start the server in debug mode."
)
parser.add_argument(
    "-H",
    "--host",
    default="127.0.0.1",
    help="Set the IP adress of the server. (Default: %(default)s)",
)
parser.add_argument(
    "-p",
    "--port",
    default=8050,
    help="Set the port of the server. (Default %(default)i)",
)
parser.add_argument(
    "-l",
    "--language",
    default=LANG,
    help="Set the language of the server. (Default %(default)s)",
)
args = parser.parse_args()
