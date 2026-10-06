from dash import html, dcc
import dash_mantine_components as dmc
import dash_ag_grid as dag
from dash_extensions import EventListener
from dash_iconify import DashIconify


import icons
import functions
import components as comp
from default_values import VERSION, DEFAULT_SETTINGS
from i18n import i18n

i18n.load_from_file("locales/de.yaml", "de")

# Definiere das Layout
# Das linke untere, welches die Tabelle enthält
fensterLinks = html.Div(
    [
        dmc.Group(
            [
                dmc.Image(src="assets/Logo.svg", w=330, maw="50%"),
                dmc.Group(
                    [
                        dmc.Button(
                            dmc.Text(i18n.get("Reset Filter"), visibleFrom="xxl"),
                            id="button-filter-reset",
                            rightSection=DashIconify(
                                icon=icons.filterOff,
                                height=20,
                            ),
                            disabled=True,
                        ),
                        dmc.Tooltip(
                            id="button-filter-reset-tooltip",
                            label=i18n.get("Reset Filter"),
                            target="#button-filter-reset",
                            hiddenFrom="xxl",
                        ),
                        dmc.Button(
                            dmc.Text(i18n.get("Edit Master Data"), visibleFrom="xl"),
                            id="button-stammdaten",
                            rightSection=DashIconify(icon=icons.edit, height=20),
                        ),
                        dmc.Tooltip(
                            id="button-stammdaten-tooltip",
                            label=i18n.get("Edit Master Data"),
                            target="#button-stammdaten",
                            hiddenFrom="xl",
                        ),
                        dmc.Button(
                            dmc.Text(i18n.get("New Entry"), visibleFrom="lg"),
                            id="button-open-modal",
                            rightSection=DashIconify(icon=icons.add, height=24),
                            n_clicks=0,
                        ),
                        comp.KbdTooltip(
                            target="#button-open-modal",
                            label=[
                                dmc.Kbd("Shift"),
                                " + ",
                                functions.system_key(),
                                " + ",
                                dmc.Kbd("E"),
                            ],
                        ),
                        dmc.Tooltip(
                            id="button-open-modal-tooltip",
                            target="#button-open-modal",
                            label=i18n.get("New Entry"),
                            hiddenFrom="lg",
                        ),
                        dmc.Tooltip(
                            dmc.ActionIcon(
                                DashIconify(
                                    icon=icons.archive,
                                    height=24,
                                ),
                                h=36,
                                w=36,
                                id="button_archive",
                                gradient={"from": "indigo", "to": "teal"},
                            ),
                            label=i18n.get("Archive"),
                        ),
                        dmc.Tooltip(
                            dmc.ActionIcon(
                                DashIconify(
                                    icon=icons.settings,
                                    height=24,
                                ),
                                h=36,
                                w=36,
                                id="button-einstellungen",
                            ),
                            label=i18n.get("Settings"),
                        ),
                    ],
                    id="button_wrapper",
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
                {
                    "field": "Barcode",
                    "sortable": True,
                    "sort": "asc",
                    "headerName": i18n.get("Barcode"),
                },
                {
                    "field": "Name",
                    "sortable": True,
                    "headerName": i18n.get("Name"),
                },
                {
                    "field": "Summenformel",
                    "cellRenderer": "SummenformelRenderer",
                    "sortable": True,
                    "headerName": i18n.get("Molecular formular"),
                },
                {
                    "field": "Zuletzt_geprüft",
                    "headerName": i18n.get("Last checked"),
                    "sortable": True,
                    "filter": "agTextColumnFilter",
                },
                {
                    "field": "Raum",
                    "sortable": True,
                    "headerName": i18n.get("Room"),
                },
                {
                    "field": "CAS",
                    "headerName": i18n.get("CAS no."),
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
                "autoSizeStrategy": {
                    "type": "fitCellContents",
                    "scaleUpToFitGridWidth": True,
                },
                "rowSelection": {  # Aktiviere das Auswählen von Zeilen
                    "mode": "singleRow",
                    "enableClickSelection": True,
                    "checkboxes": False,
                },
                "overlayComponentParams": {
                    "loading": {"overlayText": i18n.get("Loading...")},
                    "noRows": {"overlayText": i18n.get("No entries available")},
                    "noMatchingRows": {
                        "overlayText": i18n.get("No matching entries found")
                    },
                },
                "icons": {  # Vertausche die Richtung der Pfeile für das Sortieren, damit der Pfeil runterzeigt, wenn von A->Z sortiert wird
                    "sortAscending": "\u2193",  # ↓
                    "sortDescending": "\u2191",  # ↑
                },
            },
        ),
    ],
    style={"padding": "20px 5px 20px 20px"},
)

stoffeigenschaften = (
    dmc.Fieldset(
        dmc.SimpleGrid(
            [
                dmc.TextInput(id="input-cas-nr", label=i18n.get("CAS no.")),
                dmc.Group(
                    [
                        comp.NumberInput(  # Molmasse
                            "input-molmasse",
                            i18n.get("Molar mass"),
                        ),
                        dmc.TextInput(
                            id="input-summenformel",
                            label=i18n.get("Molecular formular"),
                        ),
                    ],
                    grow=True,
                ),
                dmc.Group(
                    [
                        dmc.TextInput(
                            id="input-zvg",
                            label=i18n.get("ZVG no."),
                            disabled=True,
                        ),
                        dmc.Anchor(
                            dmc.Button(
                                i18n.get("Open in GESTIS"),
                                leftSection=DashIconify(
                                    icon=icons.externalLink,
                                ),
                                disabled=True,
                                id="button_to_gestis",
                                fullWidth=True,
                            ),
                            id="anchor_to_gestis",
                            href="",
                            target="_blank",
                            underline="never",
                        ),
                    ],
                    grow=True,
                    align="end",
                ),
            ],
            cols=1,
        ),
        legend=i18n.get("Chemical properties"),
    ),
)
# Das rechte untere Hauptfenster mit den Informationen zu dem entsprechenden Stoff
fensterRechts = [
    html.Div(
        [
            dmc.ScrollAreaAutosize(
                [
                    dmc.TextInput(
                        id="input-name",
                        styles={
                            "input": {
                                "fontSize": "2em",
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
                                        label=i18n.get("Search database"),
                                    ),
                                ),
                                dmc.PopoverDropdown(
                                    dmc.Grid(
                                        [
                                            dmc.GridCol(
                                                dmc.Select(
                                                    id="input-selectFromDatabase",
                                                    comboboxProps={
                                                        "withinPortal": False
                                                    },
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
                                                    label=i18n.get("Inherit entry"),
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
                    dmc.Space(h={"base": 0, "lg": 7.5, "xl": 14.5}),
                    dmc.Fieldset(
                        dmc.SimpleGrid(
                            [
                                dmc.TextInput(
                                    id="input-barcode",
                                    label=i18n.get("Barcode"),
                                    disabled=True,
                                ),
                                dmc.Group(
                                    [
                                        comp.NumberInput(  # Füllmenge
                                            "input-füllmenge",
                                            i18n.get("Amount"),
                                            w="100%",
                                            rightSection=dmc.Select(
                                                id="input-mengeneinheit",
                                                value="1",
                                                allowDeselect=False,
                                                data=functions.generateSelectData(
                                                    functions.Units,
                                                    [
                                                        "mengeneinheit_id",
                                                        "mengeneinheit",
                                                    ],
                                                ),
                                                w=60,
                                                variant="unstyled",
                                            ),
                                            className="mengeneinheit-NumberInput",
                                        ),
                                        html.Button(
                                            dmc.Sparkline(
                                                id="füllmenge_sparkline",
                                                curveType="linear",
                                                data=[],
                                                fillOpacity=0.5,
                                                withGradient=True,
                                                h=36,
                                                w="100%",
                                                display=None,
                                                flex="1 0 auto",
                                            ),
                                            id="füllmenge_sparkline_wrapper",
                                            style={
                                                "width": "40%",
                                                "height": "auto",
                                                "flex": "1 0 auto",
                                                "padding": "0",
                                                "background": "None",
                                                "border": "None",
                                                "cursor": "help",
                                            },
                                            hidden=True,
                                        ),
                                    ],
                                    justify="space-between",
                                    align="end",
                                    wrap="nowrap",
                                    gap="xs",
                                    grow=True,
                                    preventGrowOverflow=False,
                                ),
                                comp.DateInput(
                                    "input-kaufdatum",
                                    i18n.get("Purchase date"),
                                    "input-kaufdatum-heute",
                                ),  # Kaufdatum
                                dmc.Select(  # Hersteller
                                    id="input-hersteller",
                                    value="0",
                                    label=i18n.get("Manufacturer"),
                                    searchable=True,
                                    allowDeselect=False,
                                    data=functions.generateSelectData(
                                        functions.Manufacturers,
                                        ["hersteller_id", "hersteller"],
                                    ),
                                ),
                                dmc.Select(  # Lieferant
                                    id="input-lieferant",
                                    value="0",
                                    label=i18n.get("Supplier"),
                                    searchable=True,
                                    allowDeselect=False,
                                    data=functions.generateSelectData(
                                        functions.Suppliers,
                                        ["lieferant_id", "lieferant"],
                                    ),
                                ),
                                dmc.Select(  # Raum
                                    id="input-raum",
                                    value="0",
                                    label=i18n.get("Room"),
                                    searchable=True,
                                    allowDeselect=False,
                                    data=functions.generateSelectData_Räume(),
                                ),
                                dmc.TextInput(  # Reinheit
                                    id="input-reinheit",
                                    label=i18n.get("Purity"),
                                ),
                                dmc.TextInput(  # Konzentration
                                    id="input-konzentration",
                                    label=i18n.get("Concentration"),
                                ),
                                dmc.TextInput(  # Lösungsmittel
                                    id="input-lösungsmittel",
                                    label=i18n.get("Solvent"),
                                ),
                                comp.DateInput(  # Zuletzt geprüft
                                    "input-geprüft",
                                    i18n.get("Last checked"),
                                    "input-geprüft-heute",
                                ),
                            ],
                            cols=2,
                        ),
                        legend=i18n.get("inventory"),
                    ),
                    dmc.Space(h={"base": 0, "lg": 10, "xl": 21}),
                    dmc.Fieldset(
                        dmc.SimpleGrid(
                            [
                                dmc.TextInput(
                                    id="input-cas-nr",
                                    label=i18n.get("CAS no."),
                                ),
                                dmc.Group(
                                    [
                                        comp.NumberInput(  # Molmasse
                                            "input-molmasse",
                                            i18n.get("Molar mass"),
                                        ),
                                        dmc.TextInput(
                                            id="input-summenformel",
                                            label=i18n.get("Molecular formular"),
                                        ),
                                    ],
                                    grow=True,
                                ),
                                dmc.Group(
                                    [
                                        dmc.TextInput(
                                            id="input-zvg",
                                            label=i18n.get("ZVG no."),
                                            disabled=True,
                                        ),
                                        dmc.Anchor(
                                            dmc.Button(
                                                dmc.Text(
                                                    i18n.get("Open in GESTIS"),
                                                    visibleFrom="xl",
                                                ),
                                                leftSection=DashIconify(
                                                    icon=icons.externalLink, height=20
                                                ),
                                                disabled=True,
                                                id="button_to_gestis",
                                                fullWidth=True,
                                            ),
                                            id="anchor_to_gestis",
                                            href="",
                                            target="_blank",
                                            underline="never",
                                        ),
                                    ],
                                    grow=True,
                                    align="end",
                                ),
                                dmc.Tooltip(
                                    label=i18n.get("Open in GESTIS"),
                                    target="#button_to_gestis",
                                    hiddenFrom="xl",
                                ),
                            ],
                            cols=1,
                        ),
                        legend=i18n.get("Chemical properties"),
                    ),
                ],
                mah="calc(100vh - 150px)",
            ),
            dmc.Group(
                [
                    dmc.ButtonGroup(
                        [
                            dmc.Button(
                                dmc.Text(i18n.get("Save"), visibleFrom="md"),
                                id="button-speichern",
                                color="green",
                                rightSection=DashIconify(icon=icons.save),
                                size="lg",
                                n_clicks=0,
                                flex=1,
                            ),
                            dmc.Tooltip(
                                label=i18n.get("Save"),
                                target="#button-speichern",
                                hiddenFrom="md",
                            ),
                            comp.KbdTooltip(
                                target="#button-speichern",
                                label=[dmc.Kbd("Shift"), " + ", dmc.Kbd("Enter")],
                            ),
                            dmc.Button(
                                dmc.Text(
                                    i18n.get("Put in Archive"),
                                    visibleFrom="xl",
                                ),
                                id="button_to_archive",
                                color="dark.7",
                                rightSection=DashIconify(icon=icons.archive),
                                size="lg",
                                flex=1,
                            ),
                            dmc.Tooltip(
                                label=i18n.get("Put in Archive"),
                                target="#button_to_archive",
                                hiddenFrom="xl",
                                id="button_to_archive_tooltip",
                            ),
                        ],
                        flex=1,
                    ),
                    dmc.Tooltip(
                        dmc.ActionIcon(
                            DashIconify(icon=icons.delete, color="#fff", height=20),
                            id="button-löschen",
                            color="red",
                            h=50,
                            w=50,
                        ),
                        label=i18n.get("Delete"),
                    ),
                ],
                justify="space-between",
            ),
        ],
        style={
            "display": "None",
            "flexDirection": "column",
            "justifyContent": "space-between",
            "padding": "20px 20px 20px 5px",
            "height": "100%",
        },
        id="inputContainer",
    ),
    dmc.Stack(
        [
            dmc.Image(src="assets/empty.svg", fit="contain", w=200),
            dmc.Space(h=10),
            dmc.Title(i18n.get("Nothing selected!"), fw=700, order=2),
            dmc.Text(i18n.get("Select an entry on the left")),
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
            placeholder=i18n.get("New chemical"),
            styles={
                "input": {
                    "fontSize": "2em",
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
                            label=i18n.get("Search database"),
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
                                        label=i18n.get("Inherit entry"),
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
                                    dmc.TextInput(
                                        id="modal-input-barcode",
                                        label=i18n.get("Barcode"),
                                        required=True,
                                        n_blur=0,
                                    ),
                                    dmc.Group(
                                        [
                                            comp.NumberInput(  # Füllmenge
                                                "modal-input-füllmenge",
                                                i18n.get("Amount"),
                                                w="100%",
                                                rightSection=dmc.Select(  #  Mengeneinheit
                                                    id="modal-input-mengeneinheit",
                                                    value="1",
                                                    allowDeselect=False,
                                                    data=functions.generateSelectData(
                                                        functions.Units,
                                                        [
                                                            "mengeneinheit_id",
                                                            "mengeneinheit",
                                                        ],
                                                    ),
                                                    w=60,
                                                    variant="unstyled",
                                                ),
                                                className="mengeneinheit-NumberInput",
                                            ),
                                        ],
                                        justify="space-between",
                                        align="end",
                                    ),
                                    comp.DateInput(  # Kaufdatum
                                        "modal-input-kaufdatum",
                                        i18n.get("Purchase date"),
                                        "modal-input-kaufdatum-heute",
                                    ),
                                    dmc.Select(  # Hersteller
                                        id="modal-input-hersteller",
                                        label=i18n.get("Manufacturer"),
                                        searchable=True,
                                        allowDeselect=False,
                                        value="0",
                                        data=functions.generateSelectData(
                                            functions.Manufacturers,
                                            ["hersteller_id", "hersteller"],
                                        ),
                                    ),
                                    dmc.Select(  # Lieferant
                                        id="modal-input-lieferant",
                                        label=i18n.get("Supplier"),
                                        searchable=True,
                                        allowDeselect=False,
                                        value="0",
                                        data=functions.generateSelectData(
                                            functions.Suppliers,
                                            ["lieferant_id", "lieferant"],
                                        ),
                                    ),
                                    dmc.Select(  # Raum
                                        id="modal-input-raum",
                                        label=i18n.get("Room"),
                                        searchable=True,
                                        allowDeselect=False,
                                        value="0",
                                        data=functions.generateSelectData_Räume(),
                                    ),
                                    dmc.TextInput(  # Reinheit
                                        id="modal-input-reinheit",
                                        label=i18n.get("Purity"),
                                    ),
                                    dmc.TextInput(  # Konzentration
                                        id="modal-input-konzentration",
                                        label=i18n.get("Concentration"),
                                    ),
                                    dmc.TextInput(  # Lösungsmittel
                                        id="modal-input-lösungsmittel",
                                        label=i18n.get("Solvent"),
                                    ),
                                    comp.DateInput(  # Zuletzt geprüft
                                        "modal-input-geprüft",
                                        i18n.get("Last checked"),
                                        "modal-input-geprüft-heute",
                                    ),
                                ],
                                cols=2,
                            ),
                            legend=i18n.get("inventory"),
                        ),
                    ],
                    span=8,
                ),
                dmc.GridCol(
                    children=dmc.Stack(
                        [
                            dmc.Fieldset(
                                [
                                    dmc.TextInput(
                                        id="modal-input-cas-nr",
                                        label=i18n.get("CAS no."),
                                    ),
                                    comp.NumberInput(
                                        "modal-input-molmasse",
                                        i18n.get("Molar mass"),
                                    ),
                                    dmc.TextInput(
                                        id="modal-input-summenformel",
                                        label=i18n.get("Molecular formular"),
                                    ),
                                    dmc.TextInput(
                                        id="modal-input-zvg",
                                        label=i18n.get("ZVG no."),
                                        disabled=True,
                                    ),
                                ],
                                legend=i18n.get("Chemical properties"),
                            ),
                            dmc.ButtonGroup(
                                [
                                    dmc.Button(
                                        dmc.Text(i18n.get("Save"), visibleFrom="xl"),
                                        id="modal-button-speichern",
                                        color="green",
                                        rightSection=DashIconify(icon=icons.save),
                                        size="lg",
                                        fullWidth=True,
                                        n_clicks=0,
                                    ),
                                    dmc.Tooltip(
                                        label=i18n.get("Save"),
                                        target="#modal-button-speichern",
                                        hiddenFrom="xl",
                                    ),
                                    comp.KbdTooltip(
                                        target="#modal-button-speichern",
                                        label=[
                                            dmc.Kbd("Shift"),
                                            " + ",
                                            dmc.Kbd("Enter"),
                                        ],
                                    ),
                                    dmc.Button(
                                        dmc.Text(i18n.get("Cancel"), visibleFrom="xl"),
                                        id="modal-button-abbrechen",
                                        color="red",
                                        rightSection=DashIconify(icon=icons.close),
                                        size="lg",
                                        fullWidth=True,
                                    ),
                                    dmc.Tooltip(
                                        label=i18n.get("Cancel"),
                                        target="#modal-button-abbrechen",
                                        hiddenFrom="xl",
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
                    value="manufacturers",
                    data=[
                        {"value": "manufacturers", "label": i18n.get("Manufacturer")},
                        {"value": "suppliers", "label": i18n.get("suppliers")},
                        {"value": "buildings", "label": i18n.get("Buildings")},
                        {"value": "rooms", "label": i18n.get("Rooms")},
                        {"value": "gestis", "label": i18n.get("Gestis data")},
                        {"value": "units", "label": i18n.get("Units")},
                    ],
                    id="selectStammdaten",
                    allowDeselect=False,
                    w=200,
                ),
                dmc.Group(
                    [
                        dmc.Button(
                            i18n.get("Delete row"),
                            id="stammdatenButtonZeileLöschen",
                            rightSection=DashIconify(icon=icons.delete, height=20),
                            color="red",
                        ),
                        dmc.Button(
                            i18n.get("Add row"),
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
                "filter": True,
                "floatingFilter": True,
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
                "rowSelection": {  # Aktiviere das Auswählen von Zeilen
                    "mode": "singleRow",
                    "enableClickSelection": True,
                    "checkboxes": False,
                },
            },
        ),
        dmc.Group(
            [
                dmc.Group(
                    [
                        dmc.Button(
                            i18n.get("Cancel"),
                            color="red",
                            rightSection=DashIconify(icon=icons.close, height=24),
                            id="stammdatenButtonAbbrechen",
                        ),
                        dmc.Button(
                            i18n.get("Reset changes"),
                            color="grey",
                            rightSection=DashIconify(icon=icons.refresh, height=24),
                            id="stammdatenButtonZurücksetzen",
                            disabled=True,
                        ),
                        dmc.Button(
                            i18n.get("Save changes"),
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
        dmc.Group(
            [
                dmc.Title(i18n.get("Settings"), order=2),
                dmc.Group(
                    [
                        comp.Version(VERSION).Text(),
                        comp.Version(VERSION).Badge(),
                    ],
                    gap="xs",
                ),
            ],
            justify="space-between",
        ),
        dmc.ScrollAreaAutosize(
            dmc.Stack(
                [
                    dmc.Stack(
                        [
                            dmc.Title(i18n.get("Manage database"), order=4),
                            dmc.Text(
                                i18n.get(
                                    "Import an existing database, export the currently used one, or create a new one"
                                )
                            ),
                            dmc.Group(
                                [
                                    dmc.Button(
                                        i18n.get("Export"),
                                        id="einstellung_datenbank_exportieren",
                                    ),
                                    dcc.Download(
                                        id="einstellung_datenbank_exportieren_download"
                                    ),
                                    dcc.Upload(
                                        dmc.Button(
                                            i18n.get("Import"),
                                        ),
                                        id="einstellung_datenbank_importieren_daten",
                                        accept=".sqlite",
                                    ),
                                    dmc.Button(
                                        i18n.get("Create new database"),
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
                            dmc.Title(i18n.get("Date change"), order=4),
                            dmc.Text(
                                i18n.get(
                                    'Determines whether the "Last checked" field is automatically set to today when creating or editing entries.'
                                )
                            ),
                            dmc.Select(
                                value=DEFAULT_SETTINGS.get("Datumsänderung"),
                                data=[
                                    {"value": "never", "label": i18n.get("never")},
                                    {
                                        "value": "create",
                                        "label": i18n.get("Only when creating entries"),
                                    },
                                    {
                                        "value": "change",
                                        "label": i18n.get("Only when changing entries"),
                                    },
                                    {
                                        "value": "createchange",
                                        "label": i18n.get(
                                            "Both when creating and changing entries"
                                        ),
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
                            dmc.Title(i18n.get("Frequency of local backups"), order=4),
                            dmc.Text(
                                i18n.get("Defines how often a local backup is created.")
                            ),
                            dmc.Select(
                                value=DEFAULT_SETTINGS.get("backup_häufigkeit"),
                                data=[
                                    {"value": "never", "label": i18n.get("never")},
                                    {
                                        "value": "open",
                                        "label": i18n.get(
                                            "When opening/refreshing the page"
                                        ),
                                    },
                                    {
                                        "value": "interval",
                                        "label": i18n.get("After a set time, namely"),
                                    },
                                ],
                                w="40%",
                                allowDeselect=False,
                                id="einstellung_backup_häufigkeit",
                            ),
                            dmc.Group(
                                [
                                    dmc.Text(i18n.get("Every...")),
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
                            i18n.get("Cancel"),
                            color="red",
                            rightSection=DashIconify(icon=icons.close, height=24),
                            id="einstellungenButtonAbbrechen",
                        ),
                        dmc.Button(
                            i18n.get("Reset changes"),
                            color="grey",
                            rightSection=DashIconify(icon=icons.refresh, height=24),
                            id="einstellungenButtonZurücksetzen",
                        ),
                        dmc.Button(
                            i18n.get("Save changes"),
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
        dmc.Title(i18n.get("Save database?"), order=2),
        dmc.Text(i18n.get("Should a backup of the open database be created?")),
        dmc.Group(
            [
                dmc.Button(i18n.get("Yes"), id="einstellung_datenbank_modal_ja"),
                dmc.Button(
                    i18n.get("No"), id="einstellung_datenbank_modal_nein", color="red"
                ),
                dmc.Button(
                    i18n.get("Cancel import"),
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

modal_füllmenge_verlauf_inner = dmc.Stack(
    [
        dmc.Title(i18n.get("Fill levels"), order=2),
        dmc.LineChart(
            id="füllstände_kurve",
            curveType="linear",
            dataKey="datum",
            series=[{"name": "Füllmenge", "color": "indigo"}],
            data=[],
            h=300,
        ),
    ]
)

modal_bestätigung_speichern = dmc.Stack(
    [
        dmc.Title(i18n.get("Save entry?"), order=2),
        dmc.Group(
            [
                dmc.Button(i18n.get("Yes"), id="speichern_bestätigung_ja"),
                dmc.Button(
                    i18n.get("Cancel"),
                    id="speichern_bestätigung_abbrechen",
                    variant="outline",
                    color="grey",
                ),
            ],
            grow=True,
            preventGrowOverflow=False,
        ),
        dmc.Tooltip(
            target="#speichern_bestätigung_ja",
            label=dmc.Kbd("Enter"),
        ),
    ]
)

modal_bestätigung_löschen = dmc.Stack(
    [
        dmc.Title(i18n.get("Delete entry?"), order=2),
        dmc.Group(
            [
                dmc.Button(i18n.get("Yes"), id="löschen_bestätigung_ja"),
                dmc.Button(
                    i18n.get("Cancel"),
                    id="löschen_bestätigung_abbrechen",
                    variant="outline",
                    color="grey",
                ),
            ],
            grow=True,
            preventGrowOverflow=False,
        ),
        dmc.Tooltip(
            target="#löschen_bestätigung_ja",
            label=dmc.Kbd("Enter"),
        ),
    ]
)


MantineProvider = dmc.MantineProvider(
    [
        dcc.Store(id="stammdatenCache"),
        dcc.Store(id="einstellungenCache", storage_type="local"),
        dcc.Store(id="current_db_cache"),
        dcc.Interval(
            id="einstellung_backup_häufigkeit_helper",
            disabled=True,
            interval=60000,
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
            events=[
                {
                    "event": "keydown",
                    "props": ["key", "shiftKey", "metaKey", "ctrlKey" "target.tagName"],
                }
            ],
        ),
        dmc.Grid(
            [
                dmc.GridCol(fensterLinks, span=8),
                dmc.GridCol(fensterRechts, span=4),
            ],
            id="mainWrapper",
            gutter=0,
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
        dmc.Modal(
            modal_füllmenge_verlauf_inner,
            id="modal_füllmenge_verlauf",
            size="85%",
            centered=True,
            withCloseButton=False,
            opened=False,
        ),
        dmc.Modal(
            modal_bestätigung_speichern,
            id="modal_bestätigung_speichern",
            centered=True,
            withCloseButton=False,
            opened=False,
        ),
        dmc.Modal(
            modal_bestätigung_löschen,
            id="modal_bestätigung_löschen",
            centered=True,
            withCloseButton=False,
            opened=False,
        ),
    ],
    theme={
        "fontFamily": "Lexend",
        "headings": {"fontFamily": "Lexend"},
        "breakpoints": {
            "xs": "30em",
            "sm": "48em",
            "md": "64em",
            "lg": "74em",
            "xl": "90em",
            "xxl": "104em",
        },
    },
)
