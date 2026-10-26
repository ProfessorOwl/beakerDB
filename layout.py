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

# left part of the screen which contains the button row at the top and the main table beneath it
left_window = html.Div(
    [
        dmc.Group(
            [
                dmc.Image(src="assets/Logo.svg", w=330, maw="50%"),
                dmc.Group(
                    [
                        comp.ButtonClicks(
                            dmc.Text(i18n.get("Reset Filter"), visibleFrom="xxl"),
                            id="btn_reset_filter",
                            rightSection=DashIconify(
                                icon=icons.filter_off,
                                height=20,
                            ),
                            disabled=True,
                        ),
                        dmc.Tooltip(
                            label=i18n.get("Reset Filter"),
                            target="#btn_reset_filter",
                            hiddenFrom="xxl",
                        ),
                        comp.ButtonClicks(
                            dmc.Text(i18n.get("Edit Master Data"), visibleFrom="xl"),
                            id="btn_edit_masterdata",
                            rightSection=DashIconify(icon=icons.edit, height=20),
                        ),
                        dmc.Tooltip(
                            label=i18n.get("Edit Master Data"),
                            target="#btn_edit_masterdata",
                            hiddenFrom="xl",
                        ),
                        comp.ButtonClicks(
                            dmc.Text(i18n.get("New Entry"), visibleFrom="lg"),
                            id="btn_create_new_entry",
                            rightSection=DashIconify(icon=icons.add, height=24),
                        ),
                        comp.KbdTooltip(
                            target="#btn_create_new_entry",
                            label=[
                                dmc.Kbd("Shift"),
                                " + ",
                                functions.system_key(),
                                " + ",
                                dmc.Kbd("E"),
                            ],
                        ),
                        dmc.Tooltip(
                            target="#btn_create_new_entry",
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
                                id="btn_toggle_archive",
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
                                id="btn_open_settings",
                            ),
                            label=i18n.get("Settings"),
                        ),
                    ],
                    id="wrapper_main_buttons",
                    justify="flex-end",
                ),
            ],
            justify="space-between",
            align="center",
            p="7px 0 20px 0",
        ),
        dag.AgGrid(
            id="main_table",
            getRowId="params.data.barcode",
            columnDefs=[
                {
                    "field": "barcode",
                    "sortable": True,
                    "sort": "asc",
                    "headerName": i18n.get("Barcode"),
                },
                {
                    "field": "name",
                    "sortable": True,
                    "headerName": i18n.get("Name"),
                },
                {
                    "field": "formula",
                    "cellRenderer": "SummenformelRenderer",
                    "sortable": True,
                    "headerName": i18n.get("Molecular formula"),
                },
                {
                    "field": "lastchecked",
                    "headerName": i18n.get("Last checked"),
                    "sortable": True,
                    "filter": "agTextColumnFilter",
                },
                {
                    "field": "room",
                    "sortable": True,
                    "headerName": i18n.get("Room"),
                },
                {
                    "field": "cas",
                    "headerName": i18n.get("CAS no."),
                    "sortable": True,
                },
            ],
            defaultColDef={
                "filter": True,  # The button to active a more complex filter is disabled in custom.css
                "floatingFilter": True,
            },
            style={
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
                "rowSelection": {
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
                "icons": {
                    "sortAscending": "\u2193",  # ↓
                    "sortDescending": "\u2191",  # ↑
                },
            },
        ),
    ],
    style={"padding": "20px 5px 20px 20px"},
)

right_window = [
    html.Div(
        [
            dmc.ScrollAreaAutosize(
                [
                    dmc.TextInput(
                        id="input_name",
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
                                                icon=icons.search_database,
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
                                                    id="input_database_search",
                                                    comboboxProps={
                                                        "withinPortal": False
                                                    },
                                                    searchable=True,
                                                    data=functions.generate_select_data_search(),
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
                                                        id="btn_confirm_database_search",
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
                            id="popover_database_search",
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
                                    id="input_barcode",
                                    label=i18n.get("Barcode"),
                                    disabled=True,
                                ),
                                dmc.Group(
                                    [
                                        comp.NumberInput(
                                            "input_amount",
                                            i18n.get("Amount"),
                                            w="100%",
                                            rightSection=dmc.Select(
                                                id="input_unit",
                                                value="1",
                                                allowDeselect=False,
                                                data=functions.generate_select_data(
                                                    functions.Units,
                                                    [
                                                        "unit_id",
                                                        "unit",
                                                    ],
                                                ),
                                                w=60,
                                                variant="unstyled",
                                            ),
                                            className="mengeneinheit-NumberInput",
                                        ),
                                        html.Button(
                                            dmc.Sparkline(
                                                id="sparkline_amount",
                                                curveType="linear",
                                                data=[],
                                                fillOpacity=0.5,
                                                withGradient=True,
                                                h=36,
                                                w="100%",
                                                display=None,
                                                flex="1 0 auto",
                                            ),
                                            id="wrapper_sparkline_amount",
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
                                    "input_purchasedate",
                                    i18n.get("Purchase date"),
                                    "btn_purchasedate_today",
                                ),
                                dmc.Select(
                                    id="input_manufacturer",
                                    value="0",
                                    label=i18n.get("Manufacturer"),
                                    searchable=True,
                                    allowDeselect=False,
                                    data=functions.generate_select_data(
                                        functions.Manufacturers,
                                        ["manufacturer_id", "manufacturer"],
                                    ),
                                ),
                                dmc.Select(
                                    id="input_supplier",
                                    value="0",
                                    label=i18n.get("Supplier"),
                                    searchable=True,
                                    allowDeselect=False,
                                    data=functions.generate_select_data(
                                        functions.Suppliers,
                                        ["supplier_id", "supplier"],
                                    ),
                                ),
                                dmc.Select(
                                    id="input_room",
                                    value="0",
                                    label=i18n.get("Room"),
                                    searchable=True,
                                    allowDeselect=False,
                                    data=functions.generate_select_data_rooms(),
                                ),
                                dmc.TextInput(
                                    id="input_purity",
                                    label=i18n.get("Purity"),
                                ),
                                dmc.TextInput(
                                    id="input_concentration",
                                    label=i18n.get("Concentration"),
                                ),
                                dmc.TextInput(
                                    id="input_solvent",
                                    label=i18n.get("Solvent"),
                                ),
                                comp.DateInput(
                                    "input_lastchecked",
                                    i18n.get("Last checked"),
                                    "btn_lastchecked_today",
                                ),
                            ],
                            cols=2,
                        ),
                        legend=i18n.get("Inventory"),
                    ),
                    dmc.Space(h={"base": 0, "lg": 10, "xl": 21}),
                    dmc.Fieldset(
                        dmc.SimpleGrid(
                            [
                                dmc.TextInput(
                                    id="input_cas",
                                    label=i18n.get("CAS no."),
                                ),
                                dmc.Group(
                                    [
                                        comp.NumberInput(  # Molmasse
                                            "input_molarmass",
                                            i18n.get("Molar mass"),
                                        ),
                                        dmc.TextInput(
                                            id="input_formula",
                                            label=i18n.get("Molecular formula"),
                                        ),
                                    ],
                                    grow=True,
                                ),
                                dmc.Group(
                                    [
                                        dmc.TextInput(
                                            id="input_zvg",
                                            label=i18n.get("ZVG no."),
                                            disabled=True,
                                        ),
                                        dmc.Anchor(
                                            comp.ButtonClicks(
                                                dmc.Text(
                                                    i18n.get("Open in GESTIS"),
                                                    visibleFrom="xl",
                                                ),
                                                leftSection=DashIconify(
                                                    icon=icons.external_link, height=20
                                                ),
                                                disabled=True,
                                                id="btn_open_gestis",
                                                fullWidth=True,
                                            ),
                                            id="anchor_open_gestis",
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
                                    target="#btn_open_gestis",
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
                            comp.ButtonClicks(
                                dmc.Text(i18n.get("Save"), visibleFrom="md"),
                                id="btn_save_entry",
                                color="green",
                                rightSection=DashIconify(icon=icons.save),
                                size="lg",
                                flex=1,
                            ),
                            dmc.Tooltip(
                                label=i18n.get("Save"),
                                target="#btn_save_entry",
                                hiddenFrom="md",
                            ),
                            comp.KbdTooltip(
                                target="#btn_save_entry",
                                label=[dmc.Kbd("Shift"), " + ", dmc.Kbd("Enter")],
                            ),
                            comp.ButtonClicks(
                                dmc.Text(
                                    i18n.get("Put in Archive"),
                                    visibleFrom="xl",
                                ),
                                id="btn_archive_entry",
                                color="dark.7",
                                rightSection=DashIconify(icon=icons.archive),
                                size="lg",
                                flex=1,
                            ),
                            dmc.Tooltip(
                                label=i18n.get("Put in Archive"),
                                target="#btn_archive_entry",
                                hiddenFrom="xl",
                                id="btn_archive_entry_tooltip",
                            ),
                        ],
                        flex=1,
                    ),
                    dmc.Tooltip(
                        dmc.ActionIcon(
                            DashIconify(icon=icons.delete, color="#fff", height=20),
                            id="btn_delete_entry",
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
        id="wrapper_entry",
    ),
    dmc.Stack(
        [
            dmc.Image(src="assets/empty.svg", fit="contain", w=200),
            dmc.Space(h=10),
            dmc.Title(i18n.get("Nothing selected!"), fw=700, order=2),
            dmc.Text(i18n.get("Select an entry on the left")),
        ],
        id="placeholder_entry",
        justify="center",
        align="center",
        h="90vh",
        gap="0",
        display="flex",
    ),
]

modal_new_entry = dmc.Stack(
    [
        dmc.TextInput(
            id="modal_input_name",
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
                                    icon=icons.search_database,
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
                                        id="modal_input_database_search",
                                        comboboxProps={"withinPortal": False},
                                        searchable=True,
                                        data=functions.generate_select_data_search(),
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
                                            id="modal_btn_confirm_database_search",
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
                id="modal_popover_database_search",
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
                                        id="modal_input_barcode",
                                        label=i18n.get("Barcode"),
                                        required=True,
                                        n_blur=0,
                                    ),
                                    dmc.Group(
                                        [
                                            comp.NumberInput(
                                                "modal_input_amount",
                                                i18n.get("Amount"),
                                                w="100%",
                                                rightSection=dmc.Select(
                                                    id="modal_input_unit",
                                                    value="1",
                                                    allowDeselect=False,
                                                    data=functions.generate_select_data(
                                                        functions.Units,
                                                        [
                                                            "unit_id",
                                                            "unit",
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
                                    comp.DateInput(
                                        "modal_input_purchasedate",
                                        i18n.get("Purchase date"),
                                        "modal_btn_purchasedate_today",
                                    ),
                                    dmc.Select(
                                        id="modal_input_manufacturer",
                                        label=i18n.get("Manufacturer"),
                                        searchable=True,
                                        allowDeselect=False,
                                        value="0",
                                        data=functions.generate_select_data(
                                            functions.Manufacturers,
                                            ["manufacturer_id", "manufacturer"],
                                        ),
                                    ),
                                    dmc.Select(
                                        id="modal_input_supplier",
                                        label=i18n.get("Supplier"),
                                        searchable=True,
                                        allowDeselect=False,
                                        value="0",
                                        data=functions.generate_select_data(
                                            functions.Suppliers,
                                            ["supplier_id", "supplier"],
                                        ),
                                    ),
                                    dmc.Select(
                                        id="modal_input_room",
                                        label=i18n.get("Room"),
                                        searchable=True,
                                        allowDeselect=False,
                                        value="0",
                                        data=functions.generate_select_data_rooms(),
                                    ),
                                    dmc.TextInput(
                                        id="modal_input_purity",
                                        label=i18n.get("Purity"),
                                    ),
                                    dmc.TextInput(
                                        id="modal_input_concentration",
                                        label=i18n.get("Concentration"),
                                    ),
                                    dmc.TextInput(
                                        id="modal_input_solvent",
                                        label=i18n.get("Solvent"),
                                    ),
                                    comp.DateInput(
                                        "modal_input_lastchecked",
                                        i18n.get("Last checked"),
                                        "modal_btn_lastchecked_today",
                                    ),
                                ],
                                cols=2,
                            ),
                            legend=i18n.get("Inventory"),
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
                                        id="modal_input_cas",
                                        label=i18n.get("CAS no."),
                                    ),
                                    comp.NumberInput(
                                        "modal_input_molarmass",
                                        i18n.get("Molar mass"),
                                    ),
                                    dmc.TextInput(
                                        id="modal_input_formula",
                                        label=i18n.get("Molecular formula"),
                                    ),
                                    dmc.TextInput(
                                        id="modal_input_zvg",
                                        label=i18n.get("ZVG no."),
                                        disabled=True,
                                    ),
                                ],
                                legend=i18n.get("Chemical properties"),
                            ),
                            dmc.ButtonGroup(
                                [
                                    comp.ButtonClicks(
                                        dmc.Text(i18n.get("Save"), visibleFrom="xl"),
                                        id="modal_btn_save_entry",
                                        color="green",
                                        rightSection=DashIconify(icon=icons.save),
                                        size="lg",
                                        fullWidth=True,
                                    ),
                                    dmc.Tooltip(
                                        label=i18n.get("Save"),
                                        target="#modal_btn_save_entry",
                                        hiddenFrom="xl",
                                    ),
                                    comp.KbdTooltip(
                                        target="#modal_btn_save_entry",
                                        label=[
                                            dmc.Kbd("Shift"),
                                            " + ",
                                            dmc.Kbd("Enter"),
                                        ],
                                    ),
                                    comp.ButtonClicks(
                                        dmc.Text(i18n.get("Cancel"), visibleFrom="xl"),
                                        id="modal_btn_cancel",
                                        color="red",
                                        rightSection=DashIconify(icon=icons.close),
                                        size="lg",
                                        fullWidth=True,
                                    ),
                                    dmc.Tooltip(
                                        label=i18n.get("Cancel"),
                                        target="#modal_btn_cancel",
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

modal_masterdata = dmc.Stack(
    [
        dmc.Group(
            [
                dmc.Select(
                    value="manufacturers",
                    data=[
                        {"value": "manufacturers", "label": i18n.get("Manufacturers")},
                        {"value": "suppliers", "label": i18n.get("suppliers")},
                        {"value": "buildings", "label": i18n.get("Buildings")},
                        {"value": "rooms", "label": i18n.get("Rooms")},
                        {"value": "gestis", "label": i18n.get("Gestis data")},
                        {"value": "units", "label": i18n.get("Units")},
                    ],
                    id="select_masterdata_tables",
                    allowDeselect=False,
                    w=200,
                ),
                dmc.Group(
                    [
                        comp.ButtonClicks(
                            i18n.get("Delete row"),
                            id="btn_masterdata_delete_row",
                            rightSection=DashIconify(icon=icons.delete, height=20),
                            color="red",
                        ),
                        comp.ButtonClicks(
                            i18n.get("Add row"),
                            id="btn_masterdata_add_row",
                            rightSection=DashIconify(icon=icons.add, height=24),
                        ),
                    ]
                ),
            ],
            justify="space-between",
        ),
        dag.AgGrid(
            id="masterdata_table",
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
                        comp.ButtonClicks(
                            i18n.get("Cancel"),
                            color="red",
                            rightSection=DashIconify(icon=icons.close, height=24),
                            id="btn_masterdata_cancel",
                        ),
                        comp.ButtonClicks(
                            i18n.get("Reset changes"),
                            color="grey",
                            rightSection=DashIconify(icon=icons.refresh, height=24),
                            id="btn_masterdata_reset",
                            disabled=True,
                        ),
                        comp.ButtonClicks(
                            i18n.get("Save changes"),
                            rightSection=DashIconify(icon=icons.save, height=20),
                            color="green",
                            id="btn_masterdata_save",
                            disabled=True,
                        ),
                    ]
                ),
            ],
            justify="flex-end",
        ),
    ],
)

modal_settings = dmc.Stack(
    [
        dmc.Group(
            [
                dmc.Title(i18n.get("Settings"), order=2),
                dmc.Group(
                    [
                        comp.Version(VERSION).text(),
                        comp.Version(VERSION).badge(),
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
                                    comp.ButtonClicks(
                                        i18n.get("Export"),
                                        id="settings_btn_export_database",
                                    ),
                                    dcc.Download(
                                        id="settings_download_export_database"
                                    ),
                                    dcc.Upload(
                                        comp.ButtonClicks(
                                            i18n.get("Import"),
                                        ),
                                        id="settings_btn_import_database",
                                        accept=".sqlite",
                                    ),
                                    comp.ButtonClicks(
                                        i18n.get("Create new database"),
                                        id="settings_btn_create_database",
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
                                value=DEFAULT_SETTINGS.get(
                                    "settings_select_set_date_automatically"
                                ),
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
                                id="settings_select_set_date_automatically",
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
                                value=DEFAULT_SETTINGS.get(
                                    "settings_select_backup_frequency"
                                ),
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
                                id="settings_select_backup_frequency",
                            ),
                            dmc.Group(
                                [
                                    dmc.Text(i18n.get("Every...")),
                                    dmc.NumberInput(
                                        value=DEFAULT_SETTINGS.get(
                                            "settings_input_backup_frequency"
                                        ),
                                        w=100,
                                        withAsterisk=True,
                                        min=1,
                                        clampBehavior="strict",
                                        hideControls=False,
                                        suffix=" min",
                                        id="settings_input_backup_frequency",
                                    ),
                                ],
                                display="none",
                                id="settings_wrapper_input_backup_frequency",
                            ),
                        ],
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
                        comp.ButtonClicks(
                            i18n.get("Cancel"),
                            color="red",
                            rightSection=DashIconify(icon=icons.close, height=24),
                            id="settings_btn_cancel",
                        ),
                        comp.ButtonClicks(
                            i18n.get("Reset changes"),
                            color="grey",
                            rightSection=DashIconify(icon=icons.refresh, height=24),
                            id="settings_btn_reset",
                        ),
                        comp.ButtonClicks(
                            i18n.get("Save changes"),
                            rightSection=DashIconify(icon=icons.save, height=20),
                            color="green",
                            id="settings_btn_save",
                        ),
                    ]
                ),
            ],
            justify="flex-end",
        ),
    ]
)

modal_confirm_backup = dmc.Stack(
    [
        dmc.Title(i18n.get("Save database?"), order=2),
        dmc.Text(i18n.get("Should a backup of the open database be created?")),
        dmc.Group(
            [
                comp.ButtonClicks(i18n.get("Yes"), id="backup_btn_yes"),
                comp.ButtonClicks(i18n.get("No"), id="backup_btn_no", color="red"),
                comp.ButtonClicks(
                    i18n.get("Cancel import"),
                    id="backup_btn_cancel",
                    variant="outline",
                    color="grey",
                ),
            ],
            grow=True,
            preventGrowOverflow=False,
        ),
    ]
)

modal_linechart_amount = dmc.Stack(
    [
        dmc.Title(i18n.get("Fill levels"), order=2),
        dmc.LineChart(
            id="chart_amount",
            curveType="linear",
            dataKey="date",
            series=[{"name": i18n.get("Amount"), "color": "indigo"}],
            data=[],
            h=300,
        ),
    ]
)

modal_confirm_save = dmc.Stack(
    [
        dmc.Title(i18n.get("Save entry?"), order=2),
        dmc.Group(
            [
                comp.ButtonClicks(i18n.get("Yes"), id="save_btn_yes"),
                comp.ButtonClicks(
                    i18n.get("Cancel"),
                    id="save_btn_cancel",
                    variant="outline",
                    color="grey",
                ),
            ],
            grow=True,
            preventGrowOverflow=False,
        ),
        dmc.Tooltip(
            target="#save_btn_yes",
            label=dmc.Kbd("Enter"),
        ),
    ]
)

modal_confirm_delete = dmc.Stack(
    [
        dmc.Title(i18n.get("Delete entry?"), order=2),
        dmc.Group(
            [
                comp.ButtonClicks(i18n.get("Yes"), id="delete_btn_yes"),
                comp.ButtonClicks(
                    i18n.get("Cancel"),
                    id="delete_btn_cancel",
                    variant="outline",
                    color="grey",
                ),
            ],
            grow=True,
            preventGrowOverflow=False,
        ),
        dmc.Tooltip(
            target="#delete_btn_yes",
            label=dmc.Kbd("Enter"),
        ),
    ]
)


mantine_provider = dmc.MantineProvider(
    [
        dcc.Store(id="cache_masterdata"),
        dcc.Store(id="cache_settings", storage_type="local"),
        dcc.Store(id="cache_current_database"),
        dcc.Interval(
            id="interval_backup_frequency",
            disabled=True,
            interval=60000,
            n_intervals=0,
        ),
        dmc.NotificationContainer(id="notifications", limit=5, position="bottom-left"),
        EventListener(  # Checks for the "scan" event to happen, which is introduced by a callback in callbacks.py
            id="eventlistener_scan", events=[{"event": "scan", "props": ["detail"]}]
        ),
        EventListener(  # Global keyboard shortcut listener
            id="eventlistener_keyboard",
            events=[
                {
                    "event": "keydown",
                    "props": [
                        "key",
                        "shiftKey",
                        "metaKey",
                        "ctrlKey",
                        "target.tagName",
                    ],
                }
            ],
        ),
        dmc.Grid(
            [
                dmc.GridCol(left_window, span=8),
                dmc.GridCol(right_window, span=4),
            ],
            id="wrapper_main",
            gutter=0,
        ),
        dmc.Modal(
            modal_new_entry,
            id="modal_new_entry",
            size="85%",
            centered=True,
            withCloseButton=False,
            opened=False,
        ),
        dmc.Modal(
            modal_masterdata,
            id="modal_masterdata",
            size="85%",
            centered=True,
            withCloseButton=False,
            opened=False,
        ),
        dmc.Modal(
            modal_settings,
            id="modal_settings",
            size="85%",
            centered=True,
            withCloseButton=False,
            opened=False,
        ),
        dmc.Modal(
            modal_confirm_backup,
            id="modal_confirm_backup",
            centered=True,
            withCloseButton=False,
            opened=False,
        ),
        dmc.Modal(
            modal_linechart_amount,
            id="modal_linechart_amount",
            size="85%",
            centered=True,
            withCloseButton=False,
            opened=False,
        ),
        dmc.Modal(
            modal_confirm_save,
            id="modal_confirm_save",
            centered=True,
            withCloseButton=False,
            opened=False,
        ),
        dmc.Modal(
            modal_confirm_delete,
            id="modal_confirm_delete",
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
