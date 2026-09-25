from dash import html, dcc
import dash_mantine_components as dmc
import dash_ag_grid as dag
from dash_extensions import EventListener
from dash_iconify import DashIconify


import icons
import functions
import components as comp
from default_values import VERSION, DEFAULT_SETTINGS
from i18n_modern import I18nModern
from cli import args

i18n = I18nModern(args.language)
i18n.load_from_file("locales/en.yaml", "en")
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
                            dmc.Text(i18n.get("reset_filter"), visibleFrom="xxl"),
                            id="button-filter-reset",
                            rightSection=DashIconify(
                                icon=icons.filterOff,
                                height=20,
                            ),
                            disabled=True,
                        ),
                        dmc.Tooltip(
                            id="button-filter-reset-tooltip",
                            label=i18n.get("reset_filter"),
                            target="#button-filter-reset",
                            hiddenFrom="xxl",
                        ),
                        dmc.Button(
                            dmc.Text(i18n.get("edit_masterdata"), visibleFrom="xl"),
                            id="button-stammdaten",
                            rightSection=DashIconify(icon=icons.edit, height=20),
                        ),
                        dmc.Tooltip(
                            id="button-stammdaten-tooltip",
                            label=i18n.get("edit_masterdata"),
                            target="#button-stammdaten",
                            hiddenFrom="xl",
                        ),
                        dmc.Button(
                            dmc.Text(i18n.get("create_new_entry"), visibleFrom="lg"),
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
                            label=i18n.get("create_new_entry"),
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
                            label=i18n.get("archive"),
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
                            label=i18n.get("settings"),
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
                    "headerName": i18n.get("barcode"),
                },
                {
                    "field": "Name",
                    "sortable": True,
                    "headerName": i18n.get("name_column"),
                },
                {
                    "field": "Summenformel",
                    "cellRenderer": "SummenformelRenderer",
                    "sortable": True,
                    "headerName": i18n.get("sum_formula"),
                },
                {
                    "field": "Zuletzt_geprüft",
                    "headerName": i18n.get("last_checked"),
                    "sortable": True,
                    "filter": "agTextColumnFilter",
                },
                {
                    "field": "Raum",
                    "sortable": True,
                    "headerName": i18n.get("room"),
                },
                {
                    "field": "CAS",
                    "headerName": i18n.get("cas_number"),
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
                    "loading": {"overlayText": i18n.get("loading")},
                    "noRows": {"overlayText": i18n.get("no_entries")},
                    "noMatchingRows": {"overlayText": i18n.get("no_matching_entries")},
                },
                "icons": {  # Vertausche die Richtung der Pfeile für das Sortieren, damit der Pfeil runterzeigt, wenn von A->Z sortiert wird
                    "sortAscending": "\u2193",  # ↓
                    "sortDescending": "\u2191",  # ↑
                },
                "localeText": {
                    "filterOoo": i18n.get("filter_placeholder"),
                    "applyFilter": i18n.get("filter_apply"),
                    "resetFilter": i18n.get("reset_filter"),
                    "clearFilter": i18n.get("filter_clear"),
                    "contains": i18n.get("contains"),
                    "notContains": i18n.get("not_contains"),
                    "startsWith": i18n.get("starts_with"),
                    "endsWith": i18n.get("ends_with"),
                    "equals": i18n.get("equals"),
                    "notEqual": i18n.get("not_equal"),
                    "blank": i18n.get("blank"),
                    "notBlank": i18n.get("not_blank"),
                    "inRange": i18n.get("in_range"),
                    "lessThan": i18n.get("less_than"),
                    "greaterThan": i18n.get("greater_than"),
                    "lessThanOrEqual": i18n.get("less_than_or_equal"),
                    "greaterThanOrEqual": i18n.get("greater_than_or_equal"),
                    "andCondition": i18n.get("and_condition"),
                    "orCondition": i18n.get("or_condition"),
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
                dmc.TextInput(id="input-cas-nr", label=i18n.get("cas_number")),
                dmc.Group(
                    [
                        comp.NumberInput(  # Molmasse
                            "input-molmasse",
                            i18n.get("molar_mass"),
                        ),
                        dmc.TextInput(
                            id="input-summenformel",
                            label=i18n.get("sum_formula"),
                        ),
                    ],
                    grow=True,
                ),
                dmc.Group(
                    [
                        dmc.TextInput(
                            id="input-zvg",
                            label=i18n.get("zvg_number"),
                            disabled=True,
                        ),
                        dmc.Anchor(
                            dmc.Button(
                                i18n.get("gestis_open"),
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
        legend=i18n.get("item_properties"),
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
                                        label=i18n.get("database_search"),
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
                                                    label=i18n.get("take_over_entry"),
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
                                    label=i18n.get("barcode"),
                                    disabled=True,
                                ),
                                dmc.Group(
                                    [
                                        comp.NumberInput(  # Füllmenge
                                            "input-füllmenge",
                                            i18n.get("amount"),
                                            w="100%",
                                            rightSection=dmc.Select(
                                                id="input-mengeneinheit",
                                                value="1",
                                                allowDeselect=False,
                                                data=functions.generateSelectData(
                                                    functions.Mengeneinheiten,
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
                                    i18n.get("purchase_date"),
                                    "input-kaufdatum-heute",
                                ),  # Kaufdatum
                                dmc.Select(  # Hersteller
                                    id="input-hersteller",
                                    value="0",
                                    label=i18n.get("manufacturer"),
                                    searchable=True,
                                    allowDeselect=False,
                                    data=functions.generateSelectData(
                                        functions.Hersteller,
                                        ["hersteller_id", "hersteller"],
                                    ),
                                ),
                                dmc.Select(  # Lieferant
                                    id="input-lieferant",
                                    value="0",
                                    label=i18n.get("supplier"),
                                    searchable=True,
                                    allowDeselect=False,
                                    data=functions.generateSelectData(
                                        functions.Lieferanten,
                                        ["lieferant_id", "lieferant"],
                                    ),
                                ),
                                dmc.Select(  # Raum
                                    id="input-raum",
                                    value="0",
                                    label=i18n.get("room"),
                                    searchable=True,
                                    allowDeselect=False,
                                    data=functions.generateSelectData_Räume(),
                                ),
                                dmc.TextInput(  # Reinheit
                                    id="input-reinheit",
                                    label=i18n.get("purity"),
                                ),
                                dmc.TextInput(  # Konzentration
                                    id="input-konzentration",
                                    label=i18n.get("concentration"),
                                ),
                                dmc.TextInput(  # Lösungsmittel
                                    id="input-lösungsmittel",
                                    label=i18n.get("solvent"),
                                ),
                                comp.DateInput(  # Zuletzt geprüft
                                    "input-geprüft",
                                    i18n.get("last_checked"),
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
                                    label=i18n.get("cas_number"),
                                ),
                                dmc.Group(
                                    [
                                        comp.NumberInput(  # Molmasse
                                            "input-molmasse",
                                            i18n.get("molar_mass"),
                                        ),
                                        dmc.TextInput(
                                            id="input-summenformel",
                                            label=i18n.get("sum_formula"),
                                        ),
                                    ],
                                    grow=True,
                                ),
                                dmc.Group(
                                    [
                                        dmc.TextInput(
                                            id="input-zvg",
                                            label=i18n.get("zvg_number"),
                                            disabled=True,
                                        ),
                                        dmc.Anchor(
                                            dmc.Button(
                                                dmc.Text(
                                                    i18n.get("gestis_open"),
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
                                    label=i18n.get("gestis_open"),
                                    target="#button_to_gestis",
                                    hiddenFrom="xl",
                                ),
                            ],
                            cols=1,
                        ),
                        legend=i18n.get("item_properties"),
                    ),
                ],
                mah="calc(100vh - 150px)",
            ),
            dmc.Group(
                [
                    dmc.ButtonGroup(
                        [
                            dmc.Button(
                                dmc.Text(i18n.get("save"), visibleFrom="md"),
                                id="button-speichern",
                                color="green",
                                rightSection=DashIconify(icon=icons.save),
                                size="lg",
                                n_clicks=0,
                                flex=1,
                            ),
                            dmc.Tooltip(
                                label=i18n.get("save"),
                                target="#button-speichern",
                                hiddenFrom="md",
                            ),
                            comp.KbdTooltip(
                                target="#button-speichern",
                                label=[dmc.Kbd("Shift"), " + ", dmc.Kbd("Enter")],
                            ),
                            dmc.Button(
                                dmc.Text(
                                    i18n.get("archive_button"),
                                    visibleFrom="xl",
                                ),
                                id="button_to_archive",
                                color="dark.7",
                                rightSection=DashIconify(icon=icons.archive),
                                size="lg",
                                flex=1,
                            ),
                            dmc.Tooltip(
                                label=i18n.get("archive_button"),
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
                        label=i18n.get("delete"),
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
            dmc.Title(i18n.get("nothing_selected"), fw=700, order=2),
            dmc.Text(i18n.get("select_entry_left")),
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
            placeholder=i18n.get("new_chemical"),
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
                            label=i18n.get("database_search"),
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
                                        label=i18n.get("take_over_entry"),
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
                                        label=i18n.get("barcode"),
                                        required=True,
                                        n_blur=0,
                                    ),
                                    dmc.Group(
                                        [
                                            comp.NumberInput(  # Füllmenge
                                                "modal-input-füllmenge",
                                                i18n.get("amount"),
                                                w="100%",
                                                rightSection=dmc.Select(  #  Mengeneinheit
                                                    id="modal-input-mengeneinheit",
                                                    value="1",
                                                    allowDeselect=False,
                                                    data=functions.generateSelectData(
                                                        functions.Mengeneinheiten,
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
                                        i18n.get("purchase_date"),
                                        "modal-input-kaufdatum-heute",
                                    ),
                                    dmc.Select(  # Hersteller
                                        id="modal-input-hersteller",
                                        label=i18n.get("manufacturer"),
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
                                        label=i18n.get("supplier"),
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
                                        label=i18n.get("room"),
                                        searchable=True,
                                        allowDeselect=False,
                                        value="0",
                                        data=functions.generateSelectData_Räume(),
                                    ),
                                    dmc.TextInput(  # Reinheit
                                        id="modal-input-reinheit",
                                        label=i18n.get("purity"),
                                    ),
                                    dmc.TextInput(  # Konzentration
                                        id="modal-input-konzentration",
                                        label=i18n.get("concentration"),
                                    ),
                                    dmc.TextInput(  # Lösungsmittel
                                        id="modal-input-lösungsmittel",
                                        label=i18n.get("solvent"),
                                    ),
                                    comp.DateInput(  # Zuletzt geprüft
                                        "modal-input-geprüft",
                                        i18n.get("last_checked"),
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
                                        label=i18n.get("cas_number"),
                                    ),
                                    comp.NumberInput(
                                        "modal-input-molmasse",
                                        i18n.get("molar_mass"),
                                    ),
                                    dmc.TextInput(
                                        id="modal-input-summenformel",
                                        label=i18n.get("sum_formula"),
                                    ),
                                    dmc.TextInput(
                                        id="modal-input-zvg",
                                        label=i18n.get("zvg_number"),
                                        disabled=True,
                                    ),
                                ],
                                legend=i18n.get("item_properties"),
                            ),
                            dmc.ButtonGroup(
                                [
                                    dmc.Button(
                                        dmc.Text(i18n.get("save"), visibleFrom="xl"),
                                        id="modal-button-speichern",
                                        color="green",
                                        rightSection=DashIconify(icon=icons.save),
                                        size="lg",
                                        fullWidth=True,
                                        n_clicks=0,
                                    ),
                                    dmc.Tooltip(
                                        label=i18n.get("save"),
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
                                        dmc.Text(i18n.get("cancel"), visibleFrom="xl"),
                                        id="modal-button-abbrechen",
                                        color="red",
                                        rightSection=DashIconify(icon=icons.close),
                                        size="lg",
                                        fullWidth=True,
                                    ),
                                    dmc.Tooltip(
                                        label=i18n.get("cancel"),
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
                    value="hersteller",
                    data=[
                        {"value": "hersteller", "label": i18n.get("manufacturer")},
                        {"value": "lieferanten", "label": i18n.get("supplier_master")},
                        {"value": "gebäude", "label": i18n.get("buildings")},
                        {"value": "räume", "label": i18n.get("rooms_master")},
                        {"value": "gestisdaten", "label": i18n.get("gestis_data")},
                        {"value": "mengeneinheiten", "label": i18n.get("amount_units")},
                    ],
                    id="selectStammdaten",
                    allowDeselect=False,
                    w=200,
                ),
                dmc.Group(
                    [
                        dmc.Button(
                            i18n.get("delete_row"),
                            id="stammdatenButtonZeileLöschen",
                            rightSection=DashIconify(icon=icons.delete, height=20),
                            color="red",
                        ),
                        dmc.Button(
                            i18n.get("add_row"),
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
                "localeText": {
                    "filterOoo": i18n.get("filter_placeholder"),
                    "applyFilter": i18n.get("filter_apply"),
                    "resetFilter": i18n.get("reset_filter"),
                    "clearFilter": i18n.get("filter_clear"),
                    "contains": i18n.get("contains"),
                    "notContains": i18n.get("not_contains"),
                    "startsWith": i18n.get("starts_with"),
                    "endsWith": i18n.get("ends_with"),
                    "equals": i18n.get("equals"),
                    "notEqual": i18n.get("not_equal"),
                    "blank": i18n.get("blank"),
                    "notBlank": i18n.get("not_blank"),
                    "inRange": i18n.get("in_range"),
                    "lessThan": i18n.get("less_than"),
                    "greaterThan": i18n.get("greater_than"),
                    "lessThanOrEqual": i18n.get("less_than_or_equal"),
                    "greaterThanOrEqual": i18n.get("greater_than_or_equal"),
                    "andCondition": i18n.get("and_condition"),
                    "orCondition": i18n.get("or_condition"),
                },
            },
        ),
        dmc.Group(
            [
                dmc.Group(
                    [
                        dmc.Button(
                            i18n.get("cancel"),
                            color="red",
                            rightSection=DashIconify(icon=icons.close, height=24),
                            id="stammdatenButtonAbbrechen",
                        ),
                        dmc.Button(
                            i18n.get("reset_changes"),
                            color="grey",
                            rightSection=DashIconify(icon=icons.refresh, height=24),
                            id="stammdatenButtonZurücksetzen",
                            disabled=True,
                        ),
                        dmc.Button(
                            i18n.get("save_changes"),
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
                dmc.Title(i18n.get("settings"), order=2),
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
                            dmc.Title(i18n.get("database_manage"), order=4),
                            dmc.Text(i18n.get("database_manage_description")),
                            dmc.Group(
                                [
                                    dmc.Button(
                                        i18n.get("export"),
                                        id="einstellung_datenbank_exportieren",
                                    ),
                                    dcc.Download(
                                        id="einstellung_datenbank_exportieren_download"
                                    ),
                                    dcc.Upload(
                                        dmc.Button(
                                            i18n.get("import"),
                                        ),
                                        id="einstellung_datenbank_importieren_daten",
                                        accept=".sqlite",
                                    ),
                                    dmc.Button(
                                        i18n.get("create_new_database"),
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
                            dmc.Title(i18n.get("date_change"), order=4),
                            dmc.Text(i18n.get("date_change_description")),
                            dmc.Select(
                                value=DEFAULT_SETTINGS.get("Datumsänderung"),
                                data=[
                                    {"value": "never", "label": i18n.get("never")},
                                    {
                                        "value": "create",
                                        "label": i18n.get("on_create_only"),
                                    },
                                    {
                                        "value": "change",
                                        "label": i18n.get("on_change_only"),
                                    },
                                    {
                                        "value": "createchange",
                                        "label": i18n.get("on_create_and_change"),
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
                            dmc.Title(i18n.get("backup_frequency"), order=4),
                            dmc.Text(i18n.get("backup_frequency_description")),
                            dmc.Select(
                                value=DEFAULT_SETTINGS.get("backup_häufigkeit"),
                                data=[
                                    {"value": "never", "label": i18n.get("never")},
                                    {
                                        "value": "open",
                                        "label": i18n.get("when_opening"),
                                    },
                                    {
                                        "value": "interval",
                                        "label": i18n.get("after_time"),
                                    },
                                ],
                                w="40%",
                                allowDeselect=False,
                                id="einstellung_backup_häufigkeit",
                            ),
                            dmc.Group(
                                [
                                    dmc.Text(i18n.get("all")),
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
                            i18n.get("cancel"),
                            color="red",
                            rightSection=DashIconify(icon=icons.close, height=24),
                            id="einstellungenButtonAbbrechen",
                        ),
                        dmc.Button(
                            i18n.get("reset_changes"),
                            color="grey",
                            rightSection=DashIconify(icon=icons.refresh, height=24),
                            id="einstellungenButtonZurücksetzen",
                        ),
                        dmc.Button(
                            i18n.get("save_changes"),
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
        dmc.Title(i18n.get("database_save"), order=2),
        dmc.Text(i18n.get("database_backup_question")),
        dmc.Group(
            [
                dmc.Button(i18n.get("yes"), id="einstellung_datenbank_modal_ja"),
                dmc.Button(
                    i18n.get("no"), id="einstellung_datenbank_modal_nein", color="red"
                ),
                dmc.Button(
                    i18n.get("import_cancel"),
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
        dmc.Title(i18n.get("fill_levels"), order=2),
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
        dmc.Title(i18n.get("save_entry_question"), order=2),
        dmc.Group(
            [
                dmc.Button(i18n.get("yes"), id="speichern_bestätigung_ja"),
                dmc.Button(
                    i18n.get("cancel"),
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
        dmc.Title(i18n.get("delete_entry_question"), order=2),
        dmc.Group(
            [
                dmc.Button(i18n.get("yes"), id="löschen_bestätigung_ja"),
                dmc.Button(
                    i18n.get("cancel"),
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
