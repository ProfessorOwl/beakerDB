from dash import Dash, html, dcc
import dash_mantine_components as dmc
import dash_ag_grid as dag
from dash_extensions import EventListener
from dash_iconify import DashIconify

import json
from pathlib import Path
import shutil

import icons
from callbacks import get_callbacks
import functions
import components as comp  # NOTE -  Sorgt dafür, dass die Seite neu lädt, wenn die Website bedient wird und dev_tools_hot_reload=True ist. Entweder verwerfen, Hot Reload ausstellen oder neue Lösung finden. Vielleicht Dateistruktur ändern? SQLite-Datenbank auslagern aus Dateibaum heraus?

DEFAULT_SETTINGS = json.loads(Path("default_settings.json").read_bytes())

# Definiere den Server der Datenbank
app = Dash(__name__)
app.title = "beakerDB"
app.__init__(prevent_initial_callbacks=True)

# Überprüfe, ob überhaupt beim Serverstart überhaupt eine Datenbank vorhanden ist. Wenn nicht, dann benutzte die Vorlage "blank.sqlite" um eine leere Datenbank zu erstellen.
src_path = Path("blank.sqlite")
dest_path = Path("current.sqlite")
if not Path.exists(dest_path):
    shutil.copy(src_path, dest_path)

# Das linke untere, welches die Tabelle enthält
fensterLinks = html.Div(
    [
        dmc.Group(
            [
                dmc.Image(src="assets/Logo.svg", w=330),
                dmc.Group(
                    [
                        dmc.Button(
                            "Filter zurücksetzen",
                            id="button-filter-reset",
                            rightSection=DashIconify(
                                icon=icons.filterOff,
                                height=20,
                            ),
                            disabled=True,
                        ),
                        dmc.Button(
                            "Stammdaten bearbeiten",
                            id="button-stammdaten",
                            rightSection=DashIconify(icon=icons.edit, height=20),
                        ),
                        dmc.Button(
                            "Neuer Eintrag",
                            id="button-open-modal",
                            rightSection=DashIconify(icon=icons.add, height=24),
                        ),
                        dmc.Tooltip(
                            dmc.ActionIcon(
                                DashIconify(
                                    icon=icons.settings,
                                    height=24,
                                ),
                                size="lg",
                                id="button-einstellungen",
                            ),
                            label="Einstellungen",
                        ),
                    ],
                    justify="flex-end",
                ),
            ],
            justify="space-between",
            align="center",
            p="7px 0 20px 0",
        ),
        dag.AgGrid(
            id="mainGrid",
            getRowId="params.data.Barcode",
            columnDefs=[
                {"field": "Barcode", "sortable": True, "sort": "asc"},
                {
                    "field": "CAS-Nr",
                    "sortable": True,
                },
                {"field": "Name", "flex": 1, "sortable": True},
                {
                    "field": "Summenformel",
                    "cellRenderer": "SummenformelRenderer",
                    "sortable": True,
                },
                {
                    "field": "Raum",
                    "sortable": True,
                },
            ],
            defaultColDef={
                "filter": True,  # In custom.css ist ebenso der Filterbutton ausgeblendet, sodass nur die Suchzeile angezeigt wird
                "floatingFilter": True,
            },
            style={  # Passe die Größe an das Fenster an, ziehe die anderen Elementhöhen ab
                "height": "calc(100vh - 150px)",
                "margin": "0px",
                "padding": "0px",
            },
            dashGridOptions={
                "theme": {"function": "themeQuartz.withParams({fontFamily: 'Lexend'})"},
                "suppressFieldDotNotation": True,
                "rowSelection": "single",  # Aktiviere das Auswählen von Zeilen
                "icons": {  # Vertausche die Richtung der Pfeile für das Sortieren, damit der Pfeil runterzeigt, wenn von A->Z sortiert wird
                    "sortAscending": "\u2193",  # ↓
                    "sortDescending": "\u2191",  # ↑
                },
                "localeText": {
                    "filterOoo": "Filter...",
                    "applyFilter": "Filter anwenden",
                    "resetFilter": "Filter zurücksetzen",
                    "clearFilter": "Filter löschen",
                    "contains": "enthält",
                    "notContains": "enthält nicht",
                    "startsWith": "beginnt mit",
                    "endsWith": "endet mit",
                    "equals": "gleich",
                    "notEqual": "ungleich",
                    "blank": "leer",
                    "notBlank": "nicht leer",
                    "inRange": "im Bereich",
                    "lessThan": "kleiner als",
                    "greaterThan": "größer als",
                    "lessThanOrEqual": "kleiner oder gleich",
                    "greaterThanOrEqual": "größer oder gleich",
                    "andCondition": "UND",
                    "orCondition": "ODER",
                },
            },
        ),
    ],
    style={"padding": "20px 5px 20px 20px"},
)

# Das rechte untere Hauptfenster mit den Informationen zu dem entsprechenden Stoff
fensterRechts = [
    html.Div(
        [
            dmc.TextInput(
                id="input-name",
                styles={
                    "input": {
                        "fontSize": "2em",
                        "color": "arsenic",
                        "fontWeight": "bold",
                    }
                },
                size="xl",
                rightSection=dmc.Popover(
                    [
                        dmc.PopoverTarget(
                            dmc.Tooltip(
                                dmc.ActionIcon(
                                    DashIconify(
                                        icon=icons.databaseSearch,
                                        height=24,
                                    ),
                                    variant="light",
                                    size="xl",
                                ),
                                label="Datenbank durchsuchen",
                            ),
                        ),
                        dmc.PopoverDropdown(
                            dmc.Grid(
                                [
                                    dmc.GridCol(
                                        dmc.Select(
                                            id="input-selectFromDatabase",
                                            comboboxProps={"withinPortal": False},
                                            searchable=True,
                                            data=functions.generateSelectData_Namen(),
                                            limit=20,
                                            withCheckIcon=False,
                                        ),
                                        span="auto",
                                    ),
                                    dmc.GridCol(
                                        dmc.Tooltip(
                                            dmc.ActionIcon(
                                                DashIconify(
                                                    icon=icons.download,
                                                    height=24,
                                                ),
                                                id="input-selectFromDatabaseConfirm",
                                                size="lg",
                                            ),
                                            label="Eintrag übernehmen",
                                        ),
                                        span="content",
                                    ),
                                ],
                                align="center",
                            )
                        ),
                    ],
                    id="input-popover",
                    width="27%",
                    position="left",
                    trapFocus=True,
                    withOverlay=True,
                    overlayProps={"blur": "2px"},
                    keepMounted=True,
                ),
            ),
            dmc.Space(h="21px"),
            dmc.Fieldset(
                dmc.SimpleGrid(
                    [
                        dmc.TextInput(  # Barcode
                            id="input-barcode", label="Barcode", disabled=True
                        ),
                        dmc.Group(
                            [
                                comp.NumberInput(  # Füllmenge
                                    "input-füllmenge",
                                    "Füllmenge",
                                    w="67%",
                                ),
                                dmc.Select(
                                    id="input-mengeneinheit",
                                    w="30%",
                                    value="1",
                                    allowDeselect=False,
                                    data=functions.generateSelectData(
                                        functions.Mengeneinheiten,
                                        ["mengeneinheit_id", "mengeneinheit"],
                                    ),
                                ),
                            ],
                            justify="space-between",
                            align="end",
                            gap=0,
                        ),
                        comp.DateInput(
                            "input-kaufdatum", "Kaufdatum", "input-kaufdatum-heute"
                        ),  # Kaufdatum
                        dmc.Select(  # Hersteller
                            id="input-hersteller",
                            value="0",
                            label="Hersteller",
                            searchable=True,
                            allowDeselect=False,
                            data=functions.generateSelectData(
                                functions.Hersteller, ["hersteller_id", "hersteller"]
                            ),
                        ),
                        dmc.Select(  # Lieferant
                            id="input-lieferant",
                            value="0",
                            label="Lieferant",
                            searchable=True,
                            allowDeselect=False,
                            data=functions.generateSelectData(
                                functions.Lieferanten, ["lieferant_id", "lieferant"]
                            ),
                        ),
                        dmc.Select(  # Raum
                            id="input-raum",
                            value="0",
                            label="Raum",
                            searchable=True,
                            allowDeselect=False,
                            data=functions.generateSelectData_Räume(),
                        ),
                        dmc.TextInput(  # Reinheit
                            id="input-reinheit", label="Reinheit"
                        ),
                        dmc.TextInput(  # Konzentration
                            id="input-konzentration", label="Konzentration"
                        ),
                        dmc.TextInput(  # Lösungsmittel
                            id="input-lösungsmittel", label="Lösungsmittel"
                        ),
                        comp.DateInput(  # Zuletzt geprüft
                            "input-geprüft", "Zuletzt geprüft", "input-geprüft-heute"
                        ),
                    ],
                    cols=2,
                ),
                legend="Inventar",
            ),
            dmc.Space(h="21px"),
            dmc.Fieldset(
                [
                    dmc.TextInput(id="input-cas-nr", label="CAS-Nr"),
                    comp.NumberInput(  # Molmasse
                        "input-molmasse",
                        "Molare Masse",
                    ),
                    dmc.TextInput(id="input-summenformel", label="Summenformel"),
                ],
                legend="Stoffeigenschaften",
            ),
            dmc.Space(h="21px"),
            dmc.ButtonGroup(
                [
                    dmc.Button(
                        "Speichern",
                        id="button-speichern",
                        color="green",
                        disabled=True,
                        rightSection=DashIconify(icon=icons.save),
                        size="lg",
                        fullWidth=True,
                    ),
                    dmc.Button(
                        "Löschen",
                        id="button-löschen",
                        color="red",
                        disabled=True,
                        rightSection=DashIconify(icon=icons.delete),
                        size="lg",
                        fullWidth=True,
                    ),
                ],
            ),
        ],
        style={
            "align": "stretch",
            "justify": "space-between",
            "padding": "20px 20px 20px 5px",
        },
        id="inputContainer",
        hidden=True,
    ),
    dmc.Stack(
        [
            dmc.Image(src="assets/empty.svg", fit="contain", w=200),
            dmc.Space(h=10),
            dmc.Title("Nichts ausgewählt!", fw=700, order=2),
            dmc.Text("Wähle links einen Eintrag aus"),
        ],
        id="inputPlaceholder",
        justify="center",
        align="center",
        h="90vh",
        gap="0",
        display="flex",
    ),
]

modalNeuerEintragInner = dmc.Stack(
    [
        dmc.TextInput(
            id="modal-input-name",
            placeholder="Neue Chemikalie",
            styles={
                "input": {
                    "fontSize": "2em",
                    "color": "arsenic",
                    "fontWeight": "bold",
                }
            },
            size="xl",
            rightSection=dmc.Popover(
                [
                    dmc.PopoverTarget(
                        dmc.Tooltip(
                            dmc.ActionIcon(
                                DashIconify(
                                    icon=icons.databaseSearch,
                                    height=24,
                                ),
                                variant="light",
                                size="xl",
                            ),
                            label="Datenbank durchsuchen",
                        ),
                    ),
                    dmc.PopoverDropdown(
                        dmc.Grid(
                            [
                                dmc.GridCol(
                                    dmc.Select(
                                        id="modal-input-selectFromDatabase",
                                        comboboxProps={"withinPortal": False},
                                        searchable=True,
                                        data=functions.generateSelectData_Namen(),
                                        limit=20,
                                        withCheckIcon=False,
                                    ),
                                    span="auto",
                                ),
                                dmc.GridCol(
                                    dmc.Tooltip(
                                        dmc.ActionIcon(
                                            DashIconify(
                                                icon=icons.download,
                                                height=24,
                                            ),
                                            id="modal-input-selectFromDatabaseConfirm",
                                            size="lg",
                                        ),
                                        label="Eintrag übernehmen",
                                    ),
                                    span="content",
                                ),
                            ],
                            align="center",
                        )
                    ),
                ],
                id="modal-input-popover",
                width="70%",
                position="left",
                trapFocus=True,
                withOverlay=True,
                overlayProps={"blur": "2px"},
                keepMounted=True,
            ),
        ),
        dmc.Grid(
            [
                dmc.GridCol(
                    [
                        dmc.Fieldset(
                            dmc.SimpleGrid(
                                [
                                    dmc.TextInput(  # Barcode
                                        id="modal-input-barcode",
                                        label="Barcode",
                                        required=True,
                                    ),
                                    dmc.Group(
                                        [
                                            comp.NumberInput(  # Füllmenge
                                                "modal-input-füllmenge",
                                                "Füllmenge",
                                                w="67%",
                                            ),
                                            dmc.Select(  #  Mengeneinheit
                                                id="modal-input-mengeneinheit",
                                                w="30%",
                                                value="1",
                                                allowDeselect=False,
                                                data=functions.generateSelectData(
                                                    functions.Mengeneinheiten,
                                                    [
                                                        "mengeneinheit_id",
                                                        "mengeneinheit",
                                                    ],
                                                ),
                                            ),
                                        ],
                                        justify="space-between",
                                        align="end",
                                        gap=0,
                                    ),
                                    comp.DateInput(  # Kaufdatum
                                        "modal-input-kaufdatum",
                                        "Kaufdatum",
                                        "modal-input-kaufdatum-heute",
                                    ),
                                    dmc.Select(  # Hersteller
                                        id="modal-input-hersteller",
                                        label="Hersteller",
                                        searchable=True,
                                        allowDeselect=False,
                                        value="0",
                                        data=functions.generateSelectData(
                                            functions.Hersteller,
                                            ["hersteller_id", "hersteller"],
                                        ),
                                    ),
                                    dmc.Select(  # Lieferant
                                        id="modal-input-lieferant",
                                        label="Lieferant",
                                        searchable=True,
                                        allowDeselect=False,
                                        value="0",
                                        data=functions.generateSelectData(
                                            functions.Lieferanten,
                                            ["lieferant_id", "lieferant"],
                                        ),
                                    ),
                                    dmc.Select(  # Raum
                                        id="modal-input-raum",
                                        label="Raum",
                                        searchable=True,
                                        allowDeselect=False,
                                        value="0",
                                        data=functions.generateSelectData_Räume(),
                                    ),
                                    dmc.TextInput(  # Reinheit
                                        id="modal-input-reinheit", label="Reinheit"
                                    ),
                                    dmc.TextInput(  # Konzentration
                                        id="modal-input-konzentration",
                                        label="Konzentration",
                                    ),
                                    dmc.TextInput(  # Lösungsmittel
                                        id="modal-input-lösungsmittel",
                                        label="Lösungsmittel",
                                    ),
                                    comp.DateInput(  # Zuletzt geprüft
                                        "modal-input-geprüft",
                                        "Zuletzt geprüft",
                                        "modal-input-geprüft-heute",
                                    ),
                                ],
                                cols=2,
                            ),
                            legend="Inventar",
                        ),
                    ],
                    span=8,
                ),
                dmc.GridCol(
                    children=dmc.Stack(
                        [
                            dmc.Fieldset(
                                [
                                    dmc.TextInput(  # CAS-Nr.
                                        id="modal-input-cas-nr", label="CAS-Nr"
                                    ),
                                    comp.NumberInput(  # Molmasse
                                        "modal-input-molmasse", "Molare Masse"
                                    ),
                                    dmc.TextInput(
                                        id="modal-input-summenformel",
                                        label="Summenformel",
                                    ),
                                ],
                                legend="Stoffeigenschaften",
                            ),
                            dmc.ButtonGroup(
                                [
                                    dmc.Button(
                                        "Speichern",
                                        id="modal-button-speichern",
                                        color="green",
                                        rightSection=DashIconify(icon=icons.save),
                                        size="lg",
                                        fullWidth=True,
                                    ),
                                    # dmc.Tooltip(
                                    #     target="#modal-button-speichern",
                                    #     label=[
                                    #         dmc.Kbd("Shift"),
                                    #         " + ",
                                    #         dmc.Kbd("Enter"),
                                    #     ],
                                    # ),
                                    dmc.Button(
                                        "Abbrechen",
                                        id="modal-button-abbrechen",
                                        color="red",
                                        rightSection=DashIconify(icon=icons.close),
                                        size="lg",
                                        fullWidth=True,
                                    ),
                                ]
                            ),
                        ],
                        h="100%",
                        justify="space-between",
                    ),
                    span=4,
                ),
            ],
        ),
    ]
)

modalStammdatenInner = dmc.Stack(
    [
        dmc.Group(
            [
                dmc.Select(
                    value="hersteller",
                    data=[
                        {"value": "hersteller", "label": "Hersteller"},
                        {"value": "lieferanten", "label": "Lieferanten"},
                        {"value": "gebäude", "label": "Gebäude"},
                        {"value": "räume", "label": "Räume"},
                        {"value": "gestisdaten", "label": "Gestisdaten"},
                        {"value": "mengeneinheiten", "label": "Mengeneinheiten"},
                    ],
                    id="selectStammdaten",
                    allowDeselect=False,
                    w=200,
                ),
                dmc.Group(
                    [
                        dmc.Button(
                            "Zeile löschen",
                            id="stammdatenButtonZeileLöschen",
                            rightSection=DashIconify(icon=icons.delete, height=20),
                            color="red",
                        ),
                        dmc.Button(
                            "Zeile hinzufügen",
                            id="stammdatenButtonZeileHinzufügen",
                            rightSection=DashIconify(icon=icons.add, height=24),
                        ),
                    ]
                ),
            ],
            justify="space-between",
        ),
        dag.AgGrid(
            id="stammGrid",
            defaultColDef={
                "filter": "agTextColumnFilter",
                "floatingFilter": True,
                "filterParams": {
                    # Beschränke die Filteroptionen der Spalten auf diese 4 Optionen
                    "filterOptions": ["contains"],
                    "maxNumConditions": 0,  # Blende weitere Suchkonditionen aus
                },
            },
            style={  # Passe die Größe an das Fenster an, ziehe die anderen Elementhöhen ab
                "height": "580px",
                "margin": "0px",
                "padding": "0px",
            },
            dashGridOptions={
                "theme": {"function": "themeQuartz.withParams({fontFamily: 'Lexend'})"},
                "suppressScrollOnNewData": True,
                "suppressFieldDotNotation": True,
                "rowSelection": "single",  # Aktiviere das Auswählen von Zeilen
                "localeText": {
                    "filterOoo": "Filter...",
                    "applyFilter": "Filter anwenden",
                    "resetFilter": "Filter zurücksetzen",
                    "clearFilter": "Filter löschen",
                    "contains": "enthält",
                    "notContains": "enthält nicht",
                    "startsWith": "beginnt mit",
                    "endsWith": "endet mit",
                    "equals": "gleich",
                    "notEqual": "ungleich",
                    "blank": "leer",
                    "notBlank": "nicht leer",
                    "inRange": "im Bereich",
                    "lessThan": "kleiner als",
                    "greaterThan": "größer als",
                    "lessThanOrEqual": "kleiner oder gleich",
                    "greaterThanOrEqual": "größer oder gleich",
                    "andCondition": "UND",
                    "orCondition": "ODER",
                },
            },
        ),
        dmc.Group(
            [
                dmc.Group(
                    [
                        dmc.Button(
                            "Abbrechen",
                            color="red",
                            rightSection=DashIconify(icon=icons.close, height=24),
                            id="stammdatenButtonAbbrechen",
                        ),
                        dmc.Button(
                            "Änderungen zurücksetzen",
                            color="grey",
                            rightSection=DashIconify(icon=icons.refresh, height=24),
                            id="stammdatenButtonZurücksetzen",
                            disabled=True,
                        ),
                        dmc.Button(
                            "Änderungen speichern",
                            rightSection=DashIconify(icon=icons.save, height=20),
                            color="green",
                            id="stammdatenButtonSpeichern",
                            disabled=True,
                        ),
                    ]
                ),
            ],
            justify="flex-end",
        ),
    ],
)

modalEinstellungenInner = dmc.Stack(
    [
        dmc.Title("Einstellungen", order=2),
        dmc.ScrollAreaAutosize(
            dmc.Stack(
                [
                    dmc.Stack(  # TODO - Benötigt noch die gesamte Logik
                        [
                            dmc.Title("Datenbank verwalten", order=4),
                            dmc.Text(
                                "Importiere eine vorhandene Datenbank, exportiere die momentan genutzte oder erstelle eine neue."
                            ),
                            dmc.Group(
                                [
                                    dmc.Button(
                                        "Exportieren",
                                        id="einstellung_datenbank_exportieren",
                                    ),
                                    dcc.Download(
                                        id="einstellung_datenbank_exportieren_download"
                                    ),
                                    dcc.Upload(
                                        dmc.Button(
                                            "Importieren",
                                        ),
                                        id="einstellung_datenbank_importieren_daten",
                                        accept=".sqlite",
                                    ),
                                    dmc.Button(
                                        "Neue Datenbank erstellen",
                                        id="einstellung_datenbank_neu",
                                    ),
                                ]
                            ),
                        ],
                        gap="xs",
                    ),
                    dmc.Divider(),
                    dmc.Stack(
                        [
                            dmc.Title("Datumsänderung", order=4),
                            dmc.Text(
                                'Bestimmt, ob das Feld "Zuletzt geprüft" beim Erstellen oder Ändern von Einträgen automatisch auf den heutigen Tag gesetzt wird.'
                            ),
                            dmc.Select(
                                value=DEFAULT_SETTINGS.get("Datumsänderung"),
                                data=[
                                    {"value": "never", "label": "Nie"},
                                    {
                                        "value": "create",
                                        "label": "Nur beim Erstellen von Einträgen",
                                    },
                                    {
                                        "value": "change",
                                        "label": "Nur beim Ändern von Einträgen",
                                    },
                                    {
                                        "value": "createchange",
                                        "label": "Sowohl beim Erstellen als auch beim Ändern von Einträgen",
                                    },
                                ],
                                w="40%",
                                allowDeselect=False,
                                id="einstellung_datumsänderung",
                            ),
                        ],
                        gap="xs",
                    ),
                    dmc.Divider(),
                    dmc.Stack(
                        [
                            dmc.Title("Häufigkeit lokaler Backups", order=4),
                            dmc.Text(
                                "Legt fest, wie oft ein lokales Backup erstellt wird."
                            ),
                            dmc.Select(
                                value=DEFAULT_SETTINGS.get("backup_häufigkeit"),
                                data=[
                                    {"value": "never", "label": "Nie"},
                                    {
                                        "value": "open",
                                        "label": "Beim Öffnen/Aktualisieren der Seite",
                                    },
                                    {
                                        "value": "interval",
                                        "label": "Nach einer bestimmten Zeit, und zwar:",
                                    },
                                ],
                                w="40%",
                                allowDeselect=False,
                                id="einstellung_backup_häufigkeit",
                            ),
                            dmc.Group(
                                [
                                    dmc.Text("Alle..."),
                                    dmc.NumberInput(
                                        value=DEFAULT_SETTINGS.get(
                                            "backup_häufigkeit_minuten"
                                        ),
                                        w=100,
                                        withAsterisk=True,
                                        min=1,
                                        clampBehavior="strict",
                                        hideControls=False,
                                        suffix=" min",
                                        id="einstellung_backup_häufigkeit_minuten",
                                    ),
                                ],
                                display="none",
                                id="einstellung_backup_häufigkeit_minuten_container",
                            ),
                        ],
                        id="einstellung_backup_häufigkeit_container",
                        gap="xs",
                    ),
                ]
            ),
            mah="80vh",
        ),
        dmc.Group(
            [
                dmc.Group(
                    [
                        dmc.Button(
                            "Abbrechen",
                            color="red",
                            rightSection=DashIconify(icon=icons.close, height=24),
                            id="einstellungenButtonAbbrechen",
                        ),
                        dmc.Button(
                            "Änderungen zurücksetzen",
                            color="grey",
                            rightSection=DashIconify(icon=icons.refresh, height=24),
                            id="einstellungenButtonZurücksetzen",
                        ),
                        dmc.Button(
                            "Änderungen speichern",
                            rightSection=DashIconify(icon=icons.save, height=20),
                            color="green",
                            id="einstellungenButtonSpeichern",
                        ),
                    ]
                ),
            ],
            justify="flex-end",
        ),
    ]
)

modalBestätigungImportInner = dmc.Stack(
    [
        dmc.Title("Datenbank speichern?", order=2),
        dmc.Text("Soll ein Backup der geöffneten Datenbank erstellt werden?"),
        dmc.Group(
            [
                dmc.Button("Ja", id="einstellung_datenbank_modal_ja"),
                dmc.Button("Nein", id="einstellung_datenbank_modal_nein", color="red"),
                dmc.Button(
                    "Import abbrechen",
                    id="einstellung_datenbank_modal_abbrechen",
                    variant="outline",
                    color="grey",
                ),
            ],
            grow=True,
            preventGrowOverflow=False,
        ),
    ]
)

app.layout = dmc.MantineProvider(
    [
        dcc.Store(id="stammdatenCache"),
        dcc.Store(id="einstellungenCache", storage_type="local"),
        dcc.Store(id="current_db_cache"),
        dcc.Interval(  # FIXME - Diese Komponente und das korrespondierende Callback funktionieren nicht, da n_intervals nicht inkrementiert wird, selbst wenn disabled = False und interval=10
            id="einstellung_backup_häufigkeit_helper",
            disabled=True,
            interval=1000,
            n_intervals=0,
        ),
        dmc.NotificationContainer(
            id="notification-container", limit=5, position="bottom-left"
        ),
        EventListener(  # Checks for the "scan" event to happen, which is introduced by a callback in callbacks.py
            id="scanListener", events=[{"event": "scan", "props": ["detail"]}]
        ),
        EventListener(  # Global keyboard shortcut listener
            id="keyboardListener",
            events=[{"event": "keydown", "props": ["key", "shiftKey"]}],
        ),
        dmc.Grid(
            [
                dmc.GridCol(fensterLinks, span=8),
                dmc.GridCol(fensterRechts, span=4),
            ],
            id="mainWrapper",
        ),
        dmc.Modal(
            modalNeuerEintragInner,
            id="modalNeuerEintrag",
            size="85%",
            centered=True,
            withCloseButton=False,
            opened=False,
        ),
        dmc.Modal(
            modalStammdatenInner,
            id="modalStammdaten",
            size="85%",
            centered=True,
            withCloseButton=False,
            opened=False,
        ),
        dmc.Modal(
            modalEinstellungenInner,
            id="modalEinstellungen",
            size="85%",
            centered=True,
            withCloseButton=False,
            opened=False,
        ),
        dmc.Modal(
            modalBestätigungImportInner,
            id="modalBestätigungImport",
            centered=True,
            withCloseButton=False,
            opened=False,
        ),
        # dmc.Tooltip(
        #     target="#button-speichern",
        #     label=[dmc.Kbd("Shift"), " + ", dmc.Kbd("Enter")],
        # ),
        # dmc.Tooltip(
        #     target="#button-open-modal", label=[dmc.Kbd("Shift"), " + ", dmc.Kbd("N")]
        # ),
    ],
    theme={
        "fontFamily": "Lexend",
        "headings": {"fontFamily": "Lexend"},
        "components": {"Tooltip": {"defaultProps": {"bg": "#050B18A3", "pb": 10}}},
    },
)

# Starte den Server
if __name__ == "__main__":
    get_callbacks(app)
    app.run(debug=True, port=8050, dev_tools_hot_reload=False)
