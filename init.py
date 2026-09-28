from dash import Dash

import waitress

import functions
from cli import args

functions.init_app(args.language)

# Construct the server of the database. Cannot import from layout before the app is not safely initialized
from layout import MantineProvider

app = Dash(__name__)
app.__init__(prevent_initial_callbacks=True)
app.title = "beakerDB"
app.layout = MantineProvider

from callbacks import get_callbacks

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
