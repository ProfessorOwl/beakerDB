from dash import Dash

import waitress

from callbacks import get_callbacks
import functions
from layout import MantineProvider
from cli import args

# Construct the server of the database
app = Dash(__name__)
app.__init__(prevent_initial_callbacks=True)
app.title = "beakerDB"
app.layout = MantineProvider
functions.init_app(args.language)

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
