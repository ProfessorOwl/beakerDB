from i18n_modern import I18nModern
from cli import args

i18n = I18nModern(args.language)
i18n.load_from_file("locales/en.yaml", "en")
i18n.load_from_file("locales/de.yaml", "de")
