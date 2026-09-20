from pathlib import Path
import json

VERSION = "v0.4.2"


DEFAULT_SETTINGS = json.loads(Path("default_settings.json").read_bytes())
LANG = "de"
