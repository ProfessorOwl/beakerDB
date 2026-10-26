from pathlib import Path
import json
import datetime as dt

VERSION = "v1.0.1"


DEFAULT_SETTINGS = json.loads(Path("default_settings.json").read_bytes())
TODAY = dt.date.today().isoformat()

LANG = "de"
