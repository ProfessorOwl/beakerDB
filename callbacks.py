from dash_iconify import DashIconify
from dash import (
    Input,
    Output,
    State,
    Patch,
    ctx,
    no_update,
    NoUpdate,
    ClientsideFunction,
    clientside_callback,
    set_props,
    dcc,
)
from dash.exceptions import PreventUpdate
import json
import pandas as pd
import functions

import uuid
import base64
from pathlib import Path
import dash_mantine_components as dmc
import platform
from typing import TypedDict, Any, Literal

import icons
from i18n import i18n
from default_values import DEFAULT_SETTINGS, TODAY, LANG


class Detail(TypedDict):
    scanCode: str
    qty: int


class ScanEvent(TypedDict):
    detail: Detail


class MasterdataColumnDefs(TypedDict):
    field: str
    sortable: bool
    editable: bool
    headerName: str


class CellValue(TypedDict):
    rowIndex: int
    rowId: str
    data: dict
    oldValue: str
    value: str
    colId: str
    timestamp: int


KeyboardEvent = TypedDict(
    "KeyboardEvent",
    {
        "key": str,
        "shiftKey": bool,
        "metaKey": bool,
        "ctrlKey": bool,
        "target.tagName": str,
    },
)


def get_callbacks(app):

    @app.callback(
        Output("main_table", "rowData"),
        Input("wrapper_main", "children"),
        prevent_initial_call=False,
    )
    def init_mainGrid(children) -> list[dict]:
        """Initialize the main table with fresh data from the database.
        ``wrapper_main`` as an input is just a dummy. The callback gets fired everytime wrapper_main is initialized on the website by default.


            Args:
                children: dummy input to fire the callback

            Returns:
                dict(): a dataframe converted to a dict via "records" orient
        """

        return functions.get_main_table().to_dict("records")

    @app.callback(
        Output("input_barcode", "value"),
        Output("input_amount", "value"),
        Output("input_name", "value"),
        Output("input_formular", "value"),
        Output("input_cas", "value"),
        Output("input_unit", "value"),
        Output("input_purchasedate", "value"),
        Output("input_supplier", "value"),
        Output("input_manufacturer", "value"),
        Output("input_room", "value"),
        Output("input_purity", "value"),
        Output("input_concentration", "value"),
        Output("input_molarmass", "value"),
        Output("input_solvent", "value"),
        Output("input_lastchecked", "value"),
        Output("input_zvg", "value"),
        Output("wrapper_entry", "style"),
        Output("placeholder_entry", "display"),
        Output("wrapper_sparkline_amount", "hidden"),
        Output("sparkline_amount", "data"),
        Input("main_table", "selectedRows"),
    )
    def update_entry_data(rows: list[dict]) -> tuple:
        """Refreshes every entry in ``window_right`` when a new row in the ``main_table`` is selected

        Args:
            rows (list[dict]): a dict containing every column name from ``main_table`` as a key and the value from the row as value

        Returns:
            tuple: 20 Outputs
        """

        patched_input = Patch()
        patched_input["display"] = "None"

        nothing_selected = (
            "",
            "",
            "",
            "",
            "",
            "1",
            "",
            "0",
            "0",
            "0",
            "",
            "",
            "",
            "",
            "",
            "",
            patched_input,
            "flex",
            True,
            no_update,
        )
        if not rows:
            return nothing_selected
        barcode = rows[0].get("barcode", "")

        # When the barcode is not found in the table, show the placeholder and reset every value
        if functions.select_value(barcode, "barcode", functions.Inventory) == "":
            return nothing_selected

        # Hide the sparkline by default
        hide_sparkline = True
        amount_values = []

        # Extract the last amount from the json array to put it in input_amount
        amount_raw = functions.select_value(barcode, "amount", functions.Inventory)
        if len(amount_raw or []) != 0 and amount_raw:
            amount = json.loads(amount_raw)
            amount_last_entry = amount[-1][1]
            # Only show the sparkline when it has more than one entry
            if len(amount) > 1:
                hide_sparkline = False
                amount_values = [i[1] for i in amount]
                amount_values.sort(reverse=True)
        else:
            amount_last_entry = amount_raw

        patched_input["display"] = "flex"
        return (
            barcode,
            amount_last_entry,
            *[
                functions.select_value(barcode, x, functions.Inventory)
                for x in [
                    "name",
                    "formular",
                    "cas",
                    "unit_id",
                    "purchasedate",
                    "supplier_id",
                    "manufacturer_id",
                    "room_id",
                    "purity",
                    "concentration",
                    "molarmass",
                    "solvent",
                    "lastchecked",
                    "zvg",
                ]
            ],
            patched_input,
            "None",
            hide_sparkline,
            amount_values,
        )

    @app.callback(
        Output("main_table", "rowData", allow_duplicate=True),
        Output("notifications", "sendNotifications"),
        Output("wrapper_sparkline_amount", "hidden", allow_duplicate=True),
        Output("sparkline_amount", "data", allow_duplicate=True),
        Input("btn_save_entry", "n_clicks"),
        State("input_name", "value"),
        State("input_barcode", "value"),
        State("input_amount", "value"),
        State("input_purchasedate", "value"),
        State("input_manufacturer", "value"),
        State("input_supplier", "value"),
        State("input_room", "value"),
        State("input_purity", "value"),
        State("input_concentration", "value"),
        State("input_solvent", "value"),
        State("input_cas", "value"),
        State("input_molarmass", "value"),
        State("input_formular", "value"),
        State("input_unit", "value"),
        State("input_lastchecked", "value"),
        State("input_zvg", "value"),
        State("cache_settings", "data"),
    )
    def save_entry(
        n_clicks: int,
        name: str | None,
        barcode: str,
        amount: str | None,
        purchasedate: str | None,
        manufacturer_id: str | int | None,
        supplier_id: str | int | None,
        room_id: str | int | None,
        purity: str | None,
        concentration: str | None,
        solvent: str | None,
        cas: str | None,
        molarmass: str | None,
        formular: str | None,
        unit_id: str | int | None,
        lastchecked: str | None,
        zvg: str | None,
        cache_settings_json: str,
    ) -> tuple:
        """Save every entry to the database and refresh ``main_table`` once ``btn_save_entry`` is clicked

        Args:
            n_clicks (int): dummy input to trigger the callback
            name (str):
            barcode (str):
            amount (str | None):
            purchasedate (str | None):
            manufacturer_id (str | int | None):
            supplier_id (str | int | None):
            room_id (str | int | None):
            purity (str | None):
            concentration (str | None):
            solvent (str | None):
            cas (str | None):
            molarmass (str | None):
            formular (str | None):
            unit_id (str | int | None):
            lastchecked (str | None):
            zvg (str | None):
            cache_settings (str): cache used for the settings

        Returns:
            tuple: 4 Outputs
        """

        # In case the fields are empty or "", set them to 0
        if manufacturer_id == None or "":
            manufacturer_id = 0
        if supplier_id == None or "":
            supplier_id = 0
        if room_id == None or "":
            room_id = 0
        if unit_id == None or "":
            unit_id = 0

        messages = [
            dict(
                title=i18n.get("Saved!"),
                id=str(uuid.uuid4()),
                action="show",
                icon=DashIconify(
                    color="black",
                    height=24,
                    icon=icons.check,
                ),
                bg="green.3",
                color="green.3",
            )
        ]
        if "," in str(amount) and amount:
            amount = amount.replace(",", ".")
            messages.append(
                dict(
                    title=i18n.get("Warning!"),
                    message=i18n.get('"," in capacity was replaced with ".".'),
                    id=str(uuid.uuid4()),
                    action="show",
                    icon=DashIconify(
                        color="black",
                        height=24,
                        icon=icons.error,
                    ),
                    bg="yellow.3",
                    color="yellow.3",
                )
            )
        if "," in str(molarmass) and molarmass:
            molarmass = molarmass.replace(",", ".")
            messages.append(
                dict(
                    title=i18n.get("Warning!"),
                    message=i18n.get('"," in molar mass was replaced with ".".'),
                    id=str(uuid.uuid4()),
                    action="show",
                    icon=DashIconify(
                        color="black",
                        height=24,
                        icon=icons.error,
                    ),
                    bg="yellow.3",
                    color="yellow.3",
                )
            )

        # Check if the setting is activated to set the date automatically on saving. If so, then give out a notification and do it
        cache_settings = json.loads(cache_settings_json)
        if (
            cache_settings.get("settings_select_set_date_automatically") == "change"
            or cache_settings.get("settings_select_set_date_automatically")
            == "createchange"
        ) and lastchecked != TODAY:
            lastchecked = TODAY
            set_props("input_lastchecked", {"value": lastchecked})
            messages.append(
                dict(
                    title=i18n.get("Warning!"),
                    message=i18n.get("The check date of the entry was set to today"),
                    id=str(uuid.uuid4()),
                    action="show",
                    icon=DashIconify(
                        color="black",
                        height=24,
                        icon=icons.error,
                    ),
                    bg="yellow.3",
                    color="yellow.3",
                )
            )

        # Load all entries for the amount and put in the new amount, if it is unequal to the last amount
        amount_history = functions.append_amount(
            barcode,
            lastchecked,
            amount,
        )

        hide_sparkline = True
        amount_data = (
            [i[1] for i in json.loads(amount_history)] if amount_history else []
        )
        if len(amount_data) > 1:
            hide_sparkline = False

        functions.update_row(
            barcode,
            [
                "name",
                "barcode",
                "amount",
                "purchasedate",
                "purity",
                "concentration",
                "solvent",
                "cas",
                "molarmass",
                "formular",
                "manufacturer_id",
                "supplier_id",
                "room_id",
                "unit_id",
                "lastchecked",
                "zvg",
            ],
            [
                name,
                barcode,
                amount_history,
                purchasedate,
                purity,
                concentration,
                solvent,
                cas,
                molarmass,
                formular,
                manufacturer_id,
                supplier_id,
                room_id,
                unit_id,
                lastchecked,
                zvg,
            ],
            functions.Inventory,
        )

        df = functions.get_main_table()

        return (df.to_dict("records"), messages, hide_sparkline, amount_data)

    @app.callback(
        Output("main_table", "rowData", allow_duplicate=True),
        Output("notifications", "sendNotifications", allow_duplicate=True),
        Output("main_table", "selectedRows", allow_duplicate=True),
        Output("modal_confirm_delete", "opened"),
        Input("btn_delete_entry", "n_clicks"),
        Input("delete_btn_cancel", "n_clicks"),
        Input("delete_btn_yes", "n_clicks"),
        State("main_table", "selectedRows"),
    )
    def remove_row(
        n_clicks_delete: int,
        n_clicks_cancel: int,
        n_clicks_yes: int,
        rows: list[dict],
    ) -> tuple | None:
        """Controls the logic of for deleting entries

        Args:
            n_clicks_l (int): dummy input to trigger the callback
            n_clicks_abbrechen (int): dummy input to trigger the callback
            n_clicks_ja (int): dummy input to trigger the callback
            rows (list[dict]): a dict containing every column name from ``main_table`` as a key and the value from the row as value


        Returns:
            tuple: 4 Outputs
        """

        if ctx.triggered_id == "btn_delete_entry":
            return no_update, no_update, no_update, True
        elif ctx.triggered_id == "delete_btn_cancel":
            return no_update, no_update, no_update, False
        elif ctx.triggered_id == "delete_btn_yes":
            barcode = rows[0].get("barcode", "")
            functions.delete_entry(barcode, functions.Inventory)

            # Use the global dataframe, so that the table keeps changed after a pagerefresh or on another computer
            global df
            df = functions.get_main_table()
            return (
                df.to_dict("records"),
                [
                    dict(
                        title=i18n.get("Entry deleted!"),
                        id=str(uuid.uuid4()),
                        action="show",
                        icon=DashIconify(
                            color="black",
                            height=24,
                            icon=icons.delete,
                        ),
                        bg="red.3",
                        color="red.3",
                    )
                ],
                [],
                False,
            )

    @app.callback(
        Output("modal_new_entry", "opened"),
        Output(
            "modal_btn_save_entry",
            "disabled",
            allow_duplicate=True,
        ),
        Output("modal_input_barcode", "error", allow_duplicate=True),
        Output("modal_input_name", "value"),
        Output("modal_input_barcode", "value"),
        Output("modal_input_formular", "value"),
        Output("modal_input_cas", "value"),
        Output("modal_input_unit", "value"),
        Output("modal_input_amount", "value"),
        Output("modal_input_purchasedate", "value"),
        Output("modal_input_supplier", "value"),
        Output("modal_input_manufacturer", "value"),
        Output("modal_input_room", "value"),
        Output("modal_input_purity", "value"),
        Output("modal_input_concentration", "value"),
        Output("modal_input_molarmass", "value"),
        Output("modal_input_solvent", "value"),
        Output("modal_input_lastchecked", "value"),
        Output("modal_input_barcode", "n_blur"),
        Input("btn_create_new_entry", "n_clicks"),
        Input("modal_btn_cancel", "n_clicks"),
        Input("modal_btn_save_entry", "n_clicks"),
        State("cache_settings", "data"),
        State("modal_new_entry", "opened"),
        Input("eventlistener_scan", "n_events"),
        State("eventlistener_scan", "event"),
        State("modal_masterdata", "opened"),
    )
    def open_modal_new_entry(
        n_clicks_new_entry: int,
        n_clicks_cancel: int,
        n_clicks_save: int,
        cache_settings_json: str,
        is_open: bool,
        n_events: int | None,
        event: ScanEvent,
        is_masterdata_open: bool,
    ) -> tuple:
        """
        Manage the modal ``modal_new_entry`` to create new entries.

        Args:
            n_clicks_new_entry (int): dummy input to trigger the callback
            n_clicks_cancel (int): dummy input to trigger the callback
            n_clicks_save (int): dummy input to trigger the callback
            cache_settings_json (str): the settings saved as json
            is_open (bool): if ``modal_new_entry`` is open
            n_events (int | None): dummy input to trigger the callback
            event (dict): a dict containing the
            is_masterdata_open (bool): if ``modal_masterdata`` is open

        Raises:
            PreventUpdate: in case the ``n_events`` triggers the callback but doesn't contain an event or details to it, or the modal for new entries or masterdata is open

        Returns:
            tuple: 17 Outputs
        """

        cache_settings = json.loads(cache_settings_json)
        patched_n_blur = no_update

        if (
            cache_settings.get("settings_select_set_date_automatically") == "create"
            or cache_settings.get("settings_select_set_date_automatically")
            == "createchange"
        ):
            input_lastchecked = TODAY
        else:
            input_lastchecked = ""

        if ctx.triggered_id == "eventlistener_scan":
            if not event or not event.get("detail") or is_open or is_masterdata_open:
                raise PreventUpdate
            barcode = event.get("detail").get("scanCode")
            patched_n_blur = Patch()
            patched_n_blur += 1

            if functions.select_value(barcode, "barcode", functions.Inventory) == "":
                return (
                    not is_open,
                    True,
                    None,
                    "",
                    barcode,
                    "",
                    "",
                    "1",
                    "",
                    "",
                    "0",
                    "0",
                    "0",
                    "",
                    "",
                    "",
                    "",
                    input_lastchecked,
                    patched_n_blur,
                )
            else:
                raise PreventUpdate

        return (
            not is_open,
            True,
            None,
            "",
            "",
            "",
            "",
            "1",
            "",
            "",
            "0",
            "0",
            "0",
            "",
            "",
            "",
            "",
            input_lastchecked,
            patched_n_blur,
        )

    @app.callback(
        Output("modal_input_barcode", "error", allow_duplicate=True),
        Output(
            "modal_btn_save_entry",
            "disabled",
            allow_duplicate=True,
        ),
        Input("modal_input_barcode", "n_blur"),
        State("modal_input_barcode", "value"),
    )
    def is_barcode_used(n_blur: int | None, barcode: str) -> tuple[str | None, bool]:
        """Returns a tuple with a message and a bool, if the barcode field ``modal_input_barcode``is empty or the barcode is already used

        Args:
            n_blur (int | None): dummy input to trigger the callback
            barcode (str): barcode of a new entry

        Returns:
             tuple[str | None, bool]: A tuple containing either a message if ``modal_input_barcode`` is empty or has a used barcode and a bool to trigger the error message of the input
        """

        selected = functions.select_value(barcode, "barcode", functions.Inventory)

        if "" == barcode:
            return (i18n.get("Barcode cannot be empty"), True)
        elif selected == barcode:
            return (i18n.get("Barcode is already used"), True)
        else:
            return (None, False)

    @app.callback(
        Output("main_table", "rowData", allow_duplicate=True),
        Output("notifications", "sendNotifications", allow_duplicate=True),
        Input("modal_btn_save_entry", "n_clicks"),
        State("modal_input_name", "value"),
        State("modal_input_barcode", "value"),
        State("modal_input_amount", "value"),
        State("modal_input_purchasedate", "value"),
        State("modal_input_manufacturer", "value"),
        State("modal_input_supplier", "value"),
        State("modal_input_room", "value"),
        State("modal_input_purity", "value"),
        State("modal_input_concentration", "value"),
        State("modal_input_solvent", "value"),
        State("modal_input_cas", "value"),
        State("modal_input_molarmass", "value"),
        State("modal_input_formular", "value"),
        State("modal_input_unit", "value"),
        State("modal_input_lastchecked", "value"),
        State("modal_input_zvg", "value"),
    )
    def save_new_entry(
        n_clicks: int,
        name: str | None,
        barcode: str,
        amount: str | None,
        purchasedate: str | None,
        manufacturer_id: str | int | None,
        supplier_id: str | int | None,
        room_id: str | int | None,
        purity: str | None,
        concentration: str | None,
        solvent: str | None,
        cas: str | None,
        molarmass: str | None,
        formular: str | None,
        unit_id: str | int | None,
        lastchecked: str | None,
        zvg: str | None,
    ) -> tuple:
        """Save the new entry made in ``modal_new_entry`` to the database, update ``main_table`` and give out a notification

        Args:
            n_clicks (int): dummy input to trigger the callback
            name (str | None):
            barcode (str):
            amount (str | None):
            purchasedate (str | None):
            manufacturer_id (str | int | None):
            supplier_id (str | int | None):
            room_id (str | int | None):
            purity (str | None):
            concentration (str | None):
            solvent (str | None):
            cas (str | None):
            molarmass (str | None):
            formular (str | None):
            unit_id (str | int | None):
            lastchecked (str | None):
            zvg (str | None):

        Returns:
            tuple: 2 Outputs (``rowData``, ``sendNotifications``)
        """

        # In case the fields are empty or "", set them to 0
        if manufacturer_id == None or "":
            manufacturer_id = 0
        if supplier_id == None or "":
            supplier_id = 0
        if room_id == None or "":
            room_id = 0
        if unit_id == None or "":
            unit_id = 0

        # "" leads to an error, so set them to None
        if amount == "":
            amount = None
        if molarmass == "":
            molarmass = None

        messages = [
            dict(
                title=i18n.get("New entry saved!"),
                id=str(uuid.uuid4()),
                action="show",
                icon=DashIconify(
                    color="black",
                    height=24,
                    icon=icons.check,
                ),
                bg="green.3",
                color="green.3",
            )
        ]

        # FIXME - This should be changed when people use the english version, since "." is their decimal delimiter. The component should then also display a dot. Maybe this shouldnt be output at all, because it is not really interesting
        if "," in str(amount) and amount:
            amount = amount.replace(",", ".")
            messages.append(
                dict(
                    title=i18n.get("Warning!"),
                    message=i18n.get('"," in amount was replaced with a ".".'),
                    id=str(uuid.uuid4()),
                    action="show",
                    icon=DashIconify(
                        color="black",
                        height=24,
                        icon=icons.error,
                    ),
                    bg="yellow.3",
                    color="yellow.3",
                )
            )

        if "," in str(molarmass) and molarmass:
            molarmass = molarmass.replace(",", ".")
            messages.append(
                dict(
                    title=i18n.get("Warning!"),
                    message=i18n.get('"," in molar mass was replaced with a ".".'),
                    id=str(uuid.uuid4()),
                    action="show",
                    icon=DashIconify(
                        color="black",
                        height=24,
                        icon=icons.error,
                    ),
                    bg="yellow.3",
                    color="yellow.3",
                )
            )
        # Load all entries for the amount and put in the new amount, if it is unequal to the last amount
        amount_history = functions.append_amount(
            barcode,
            lastchecked,
            amount,
        )

        functions.create_row(
            [
                "name",
                "barcode",
                "amount",
                "purchasedate",
                "purity",
                "concentration",
                "solvent",
                "cas",
                "molarmass",
                "formular",
                "manufacturer_id",
                "supplier_id",
                "room_id",
                "unit_id",
                "lastchecked",
                "zvg",
            ],
            [
                name,
                barcode,
                amount_history,
                purchasedate,
                purity,
                concentration,
                solvent,
                cas,
                molarmass,
                formular,
                manufacturer_id,
                supplier_id,
                room_id,
                unit_id,
                lastchecked,
                zvg,
            ],
            functions.Inventory(),
        )

        global df  # Use the global dataframe, so that the table keeps changed after a pagerefresh or on another computer
        df = functions.get_main_table()
        return (
            df.to_dict("records"),
            messages,
        )

    @app.callback(
        Output("notifications", "clean", allow_duplicate=True),
        Input("modal_masterdata", "opened"),
    )
    def clear_notifications(is_open: bool) -> Literal[True]:
        """Delete all notifications in the the queue and currently displayed when the modal is opened or closed

        Args:
            is_open (bool): dummy input to trigger the callback when ``modal_masterdata`` gets opened or closed

        Returns:
            bool: True
        """

        return True

    @app.callback(
        Output("modal_masterdata", "opened"),
        Output("masterdata_table", "columnDefs"),
        Output("masterdata_table", "rowData"),
        Output("cache_masterdata", "data", allow_duplicate=True),
        Output("notifications", "clean"),
        Output("btn_masterdata_reset", "disabled"),
        Output("btn_masterdata_save", "disabled"),
        Input("btn_edit_masterdata", "n_clicks"),
        Input("btn_masterdata_reset", "n_clicks"),
        Input("btn_masterdata_cancel", "n_clicks"),
        Input("select_masterdata_tables", "value"),
        State("modal_masterdata", "opened"),
    )
    def open_modal_masterdata(
        n_clicks_masterdata: int,
        n_clicks_reset: int,
        n_clicks_cancel: int,
        selector: str,
        is_open: bool,
    ) -> tuple:
        """Open and close the modal, in which the master data gets edited.
        Initialize the master table with the last value of the selector.
        Reset the master table, when ``btn_masterdata_reset`` gets clicked.

        Args:
            n_clicks_masterdata (int): dummy input to trigger the callback when ``btn_edit_masterdata`` gets clicked
            n_clicks_reset (int): dummy to trigger the callback when ``btn_masterdata_reset`` gets clicked
            n_clicks_cancel (int): dummy to trigger the callback when ``btn_masterdata_cancel`` gets clicked
            selector (str): selector with every table containing masterdata
            is_open (bool): if the modal is open or not

        Returns:
            tuple: 7 Outputs
        """

        if ctx.triggered_id == "btn_masterdata_cancel":
            return (
                not is_open,
                no_update,
                no_update,
                no_update,
                no_update,
                True,
                no_update,
            )
        df = pd.read_sql(
            f"SELECT * from {selector}",
            "sqlite:///current.sqlite",
            dtype_backend="pyarrow",
        )
        headings = functions.get_table_headings(selector)
        cache = dict()
        column_defs = [
            {
                "field": i,
                "sortable": True,
                "editable": True,
                "headerName": getattr(
                    functions.masterdata_tables[selector], i.lower()
                ).doc,
            }
            for i in headings
        ]

        # Let the last column take up the remaining space
        column_defs[-1].update({"flex": True})

        # Set the first column as not-editable
        column_defs[0].update({"editable": False})

        # Use the names of the available buildings in a select component
        # instead of only the building ID
        if column_defs[1].get("field") == "building_id":
            label_value = functions.generate_select_data(
                functions.Buildings, ["building_id", "building"]
            )

            data_lookup = {i.get("value"): i.get("label") for i in label_value}

            # Create a list for the select component.
            # The ID is at the beginning to create unique lables
            # The labels can then be extracted again at a later point
            data = [i.get("value", "") + ": " + i.get("label", "") for i in label_value]

            # Change the ID column, so that the names align with the values of the selector
            df["building_id"] = df["building_id"].map(
                lambda x: str(x) + ": " + str(data_lookup.get(str(x)))
            )

            # Update the properties of the column
            column_defs[1].update(
                {
                    "cellEditor": {"function": "AllFunctionalComponentEditors"},
                    "cellEditorParams": {
                        "component": dmc.Select(
                            data=data,
                            allowDeselect=False,
                        ),
                    },
                    # cellEditorPopup: True is mandatory so that the selector doesn't clip the cell
                    "cellEditorPopup": True,
                }
            )

        if ctx.triggered_id == "btn_masterdata_reset":
            return (
                no_update,
                column_defs,
                df.to_dict("records"),
                json.dumps(cache),
                True,
                True,
                True,
            )

        if ctx.triggered_id == "select_masterdata_tables":
            return (
                no_update,
                column_defs,
                df.to_dict("records"),
                json.dumps(cache),
                True,
                True,
                True,
            )

        return (
            not is_open,
            column_defs,
            df.to_dict("records"),
            json.dumps(cache),
            no_update,
            True,
            True,
        )

    @app.callback(
        Output("masterdata_table", "rowTransaction"),
        Output("masterdata_table", "deleteSelectedRows"),
        Output("cache_masterdata", "data", allow_duplicate=True),
        Output("btn_masterdata_reset", "disabled", allow_duplicate=True),
        Output("btn_masterdata_save", "disabled", allow_duplicate=True),
        Input("btn_masterdata_add_row", "n_clicks"),
        Input("btn_masterdata_delete_row", "n_clicks"),
        State("masterdata_table", "rowData"),
        State("masterdata_table", "columnDefs"),
        State("cache_masterdata", "data"),
        State("masterdata_table", "selectedRows"),
    )
    def masterdata_manage_rows(
        n_clicks_add_row: int,
        n_clicks_delete_row: int,
        row_data: list[dict[str, Any]],
        column_defs: list[MasterdataColumnDefs],
        cache_masterdata_json: str,
        selected_rows: list[dict],
    ) -> tuple | None:
        """Add or remove lines to one of the tables in ``masterdata_table``
        Save all changes or reset them.

        Args:
            n_clicks_add_row (int): dummy input to trigger the callback by clicking on ``btn_masterdata_add_row``
            n_clicks_delete_row (int): dummy input to trigger the callback by clicking on ``btn_masterdata_delete_row``
            rowData (list[dict[str, Any]]): data from the table containing a list of every row. Each row is represented as a dict with the column names as keys and then the respective value
            columnDefs (list[masterdata_columnDefs]): the column definitions
            cache_masterdata_json (str): cache of every edit that has been done to the masterdata table
            selectedRows (list[dict]): the currently selected row, for deletion

        Returns:
            tuple | None: 5 Outputs
        """

        if selected_rows:
            selected_row = selected_rows[0]
        cache_masterdata = json.loads(cache_masterdata_json)
        first_column_name = column_defs[0].get("field")
        first_column_entries = [row[first_column_name] for row in row_data]
        first_column_entries.sort()

        # Find an unsed ID
        unused_id = None
        if first_column_entries == []:
            unused_id = 1
        else:
            for i in range(len(first_column_entries) - 1):
                diff = first_column_entries[i + 1] - first_column_entries[i]
                if diff > 1:
                    unused_id = first_column_entries[i] + 1
        if unused_id == None:
            unused_id = first_column_entries[-1] + 1

        if ctx.triggered_id == "btn_masterdata_add_row":
            # Check, if the row was edited before and is therefore already in the cache
            # Otherwise, .get throws an error
            if isinstance(cache_masterdata.get(str(unused_id)), dict):
                if "Delete" in cache_masterdata.get(str(unused_id)).get("op"):
                    cache_masterdata.update({str(unused_id): {"op": "Update"}})
            else:
                cache_masterdata.update({str(unused_id): {"op": "Insert"}})
            return (
                {"add": [{first_column_name: unused_id}]},
                no_update,
                json.dumps(cache_masterdata),
                False,
                False,
            )

        first_column_id = str(selected_row.get(first_column_name))

        if ctx.triggered_id == "btn_masterdata_delete_row":
            # Check again, if the edited row is already in the cache
            if isinstance(
                cache_masterdata.get(str(selected_row.get(first_column_name))), dict
            ):
                # Delete the row from the cache when it was has "Insert" as "op"
                if not "Update" == cache_masterdata.get(first_column_id).get("op"):
                    cache_masterdata.pop(first_column_id)
                    if cache_masterdata == {}:
                        is_disabled = True
                    else:
                        is_disabled = False
                    return (
                        no_update,
                        True,
                        json.dumps(cache_masterdata),
                        is_disabled,
                        is_disabled,
                    )

            # If the row is not with "Insert" in the cache, then save it with "Delete" as "op" to the cache
            cache_masterdata.update(
                {
                    first_column_id: {
                        first_column_name: first_column_id,
                        "op": "Delete",
                    }
                }
            )
            return (no_update, True, json.dumps(cache_masterdata), False, False)

    @app.callback(
        Output("btn_masterdata_delete_row", "disabled", allow_duplicate=True),
        Input("masterdata_table", "selectedRows"),
        State("masterdata_table", "columnDefs"),
    )
    def masterdata_toggle_delete_button(
        selected_rows: list[dict], column_defs: list[MasterdataColumnDefs]
    ) -> bool:
        """Toggle the delete button ``btn_masterdata_delete_row`` in the masterdata modal, if a row with an ID of 0 is selected

        Args:
            selected_rows (list[dict]): input to fire the callback. The ID is taken from this row
            column_defs (list[masterdata_columnDefs]): to extract the name of the first column in which the ID is

        Returns:
            bool: _description_
        """

        if selected_rows:
            selected_row = selected_rows[0]
        first_column_name = column_defs[0].get("field")
        selected_row_id = selected_row.get(first_column_name)

        if selected_row_id == 0:
            return True
        else:
            return False

    @app.callback(
        Output("cache_masterdata", "data", allow_duplicate=True),
        Output("btn_masterdata_reset", "disabled", allow_duplicate=True),
        Output("btn_masterdata_save", "disabled", allow_duplicate=True),
        Input("masterdata_table", "cellValueChanged"),
        State("cache_masterdata", "data"),
        State("masterdata_table", "columnDefs"),
    )
    def masterdata_save_cache_on_change(
        cell_value: list[CellValue],
        cache_masterdata_json: str,
        column_defs: list[MasterdataColumnDefs],
    ) -> tuple[str, bool, bool]:
        """Save the values to the cache ``cache_masterdata``, when an entry gets edited

        Args:
            cell_value (list[CellValue]): triggers the callback and contains information about the changed cell value and its row
            cache_masterdata_json (str): cache to save the edited masterdata in
            column_defs (list[MasterdataColumnDefs]): column definitons of the masterdata tale

        Returns:
            tuple[str, bool, bool]: 3 Outputs
        """

        first_column_name = column_defs[0].get("field")
        value = str(cell_value[0].get("data").get(first_column_name))
        cache_masterdata = json.loads(cache_masterdata_json)

        # Check if the edited row is already in the cache. If so, then it has been edited before
        if isinstance(cache_masterdata.get(value), dict):
            previous_op = cache_masterdata[value].get("op")
            cache_masterdata[value] = cell_value[0].get("data")
            cache_masterdata[value]["op"] = previous_op
        else:
            cache_masterdata.update({value: cell_value[0].get("data")})
            cache_masterdata[value]["op"] = "Update"

        if cache_masterdata == {}:
            is_disabled = True
        else:
            is_disabled = False

        return json.dumps(cache_masterdata), is_disabled, is_disabled

    @app.callback(
        Output("cache_masterdata", "data", allow_duplicate=True),
        Output("notifications", "sendNotifications", allow_duplicate=True),
        Output("btn_masterdata_reset", "disabled", allow_duplicate=True),
        Output("btn_masterdata_save", "disabled", allow_duplicate=True),
        Input("btn_masterdata_save", "n_clicks"),
        State("select_masterdata_tables", "value"),
        State("cache_masterdata", "data"),
    )
    def save_masterdata(
        n_clicks: int, selector: str, cache_masterdata_json: str
    ) -> tuple:
        """Saves the changed rows from masterdata to the database

        Args:
            n_clicks (int): dummy input to trigger the callback
            selector (str): selector with every table containing masterdata
            cache_masterdata_json (str): cache to use for the masterdata

        Returns:
            tuple: 4 Outputs
        """

        cache_masterdata = json.loads(cache_masterdata_json)
        messages = []
        modify_cache = cache_masterdata.copy()
        correctly_saved = set()

        for id, cached in cache_masterdata.items():
            columns = []
            values = []
            for c, v in cached.items():
                if c != "op":
                    # The column "building_id" in the table "rooms" doesnt actually contain an ID, but a joined string from id and value. Extract the ID before saving
                    columns.append(c)
                    if c == "building_id":
                        try:
                            values.append(v.split(":")[0])
                        # In the table "buildings", the column "building_id" is a normal integer id, so it doesn't need to be split
                        except:
                            values.append(v)
                    else:
                        values.append(v)
                if c == "op":
                    op = v

            # Append a message in case an error happens
            if len(columns) == 0:
                messages.append(
                    dict(
                        title=i18n.get("Rows must not contain empty entries!"),
                        message=i18n.get(
                            "The row with ID ${id} was not saved. Edit the row content or it will be discarded.",
                            values={"id": id},
                        ),
                        id=str(uuid.uuid4()),
                        action="show",
                        icon=DashIconify(
                            color="black",
                            height=24,
                            icon=icons.error,
                        ),
                        bg="yellow.3",
                        color="yellow.3",
                        autoClose=False,
                    )
                )
                continue

            # Go through the different types of operations that should be performed on the table rows
            if op == "Update":
                try:
                    functions.update_masterdata_entry(selector, columns, values)
                    modify_cache.pop(id)
                    correctly_saved.add(id)
                except Exception as e:
                    messages.append(
                        dict(
                            title=i18n.get(
                                "Error updating entry with ID ${id}", values={"id": id}
                            ),
                            message=functions.masterdata_error_parser(e),
                            id=str(uuid.uuid4()),
                            action="show",
                            icon=DashIconify(
                                color="black",
                                height=24,
                                icon=icons.error,
                            ),
                            bg="red.3",
                            color="red.3",
                            autoClose=False,
                        )
                    )
            elif op == "Delete":
                try:
                    functions.delete_masterdata_entry(selector, values)
                    modify_cache.pop(id)
                    correctly_saved.add(id)
                except Exception as e:
                    messages.append(
                        dict(
                            title=i18n.get(
                                "Error deleting entry with ID ${id}", values={"id": id}
                            ),
                            message=functions.masterdata_error_parser(e),
                            id=str(uuid.uuid4()),
                            action="show",
                            icon=DashIconify(
                                color="black",
                                height=24,
                                icon=icons.error,
                            ),
                            bg="red.3",
                            color="red.3",
                            autoClose=False,
                        )
                    )
            elif op == "Insert":
                try:
                    functions.insert_masterdata_entry(selector, columns, values)
                    modify_cache.pop(id)
                    correctly_saved.add(id)
                except Exception as e:
                    messages.append(
                        dict(
                            title=i18n.get(
                                "Error inserting entry with ID ${id}", values={"id": id}
                            ),
                            message=functions.masterdata_error_parser(e),
                            id=str(uuid.uuid4()),
                            action="show",
                            icon=DashIconify(
                                color="black",
                                height=24,
                                icon=icons.error,
                            ),
                            bg="red.3",
                            color="red.3",
                            autoClose=False,
                        )
                    )
            else:
                messages.append(
                    dict(
                        title=i18n.get("Error"),
                        message=i18n.get(
                            'The operation "${op}" could not be found for ID ${id}.',
                            values={"op": op, "id": id},
                        ),
                        id=str(uuid.uuid4()),
                        action="show",
                        icon=DashIconify(
                            color="black",
                            height=24,
                            icon=icons.error,
                        ),
                        bg="red.3",
                        color="red.3",
                        autoClose=False,
                    )
                )

        # If the cache is empty after doing all these operations, then disable the reset and the save button
        if modify_cache == {}:
            is_disabled = True
        else:
            is_disabled = False

        # Give out this notification if there is only one entry that was correctly saved
        if len(correctly_saved) == 1:
            for id in correctly_saved:
                messages.append(
                    dict(
                        title=i18n.get("Saved!"),
                        message=i18n.get(
                            "The entry with ID ${id} was correctly saved.",
                            values={id: id},
                        ),
                        id=str(uuid.uuid4()),
                        action="show",
                        icon=DashIconify(
                            color="black",
                            height=24,
                            icon=icons.check,
                        ),
                        bg="green.3",
                        color="green.3",
                        autoClose=False,
                    )
                )
        # And this in case there were more than 1
        elif len(correctly_saved) > 1:
            ids_joined = ""
            for id in correctly_saved:
                ids_joined += f"{id}, "
            ids_joined = ids_joined.rstrip(", ")
            messages.append(
                dict(
                    title=i18n.get("Saved!"),
                    message=i18n.get(
                        "The entries with IDs ${ids} were correctly saved.",
                        values={id: ids_joined},
                    ),
                    id=str(uuid.uuid4()),
                    action="show",
                    icon=DashIconify(
                        color="black",
                        height=24,
                        icon=icons.check,
                    ),
                    bg="green.3",
                    color="green.3",
                    autoClose=False,
                )
            )
        return json.dumps(modify_cache), messages, is_disabled, is_disabled

    @app.callback(
        Output("input_database_search", "data"),
        Output("input_unit", "data"),
        Output("input_manufacturer", "data"),
        Output("input_supplier", "data"),
        Output("input_room", "data"),
        Output("modal_input_database_search", "data"),
        Output("modal_input_unit", "data"),
        Output("modal_input_manufacturer", "data"),
        Output("modal_input_supplier", "data"),
        Output("modal_input_room", "data"),
        Input("btn_masterdata_save", "n_clicks"),
        Input("btn_save_entry", "n_clicks"),
    )
    def update_fields_from_masterdata(
        n_clicks_masterdata: int, n_clicks_save: int
    ) -> tuple:
        """After saving the masterdata, update every select component that depends on its data (database_search, units, manufacturers, suppliers and rooms).

        Args:
            n_clicks_masterdata (int): dummy input to trigger the callback when ``btn_masterdata_save`` is clicked
            n_clicks_save (int): dummy input to trigger the callback when ``btn_save_entry`` is clicked

        Returns:
            tuple: 10 Outputs
        """

        if ctx.triggered_id == "btn_masterdata_save":
            return (
                functions.generate_select_data_search(),
                functions.generate_select_data(
                    functions.Units,
                    ["unit_id", "unit"],
                ),
                functions.generate_select_data(
                    functions.Manufacturers, ["manufacturer_id", "manufacturer"]
                ),
                functions.generate_select_data(
                    functions.Suppliers, ["supplier_id", "supplier"]
                ),
                functions.generate_select_data_rooms(),
                functions.generate_select_data_search(),
                functions.generate_select_data(
                    functions.Units,
                    ["unit_id", "unit"],
                ),
                functions.generate_select_data(
                    functions.Manufacturers, ["manufacturer_id", "manufacturer"]
                ),
                functions.generate_select_data(
                    functions.Suppliers, ["supplier_id", "supplier"]
                ),
                functions.generate_select_data_rooms(),
            )
        else:
            return (
                functions.generate_select_data_search(),
                no_update,
                no_update,
                no_update,
                no_update,
                functions.generate_select_data_search(),
                no_update,
                no_update,
                no_update,
                no_update,
            )

    #!SECTION

    # Initialize the script for the barcode scanner, which discerns between normal keyboard input and typed input.
    clientside_callback(
        ClientsideFunction(namespace="helper", function_name="initScanner"),
        Output("eventlistener_scan", "id"),
        Input("eventlistener_scan", "id"),
        Input("modal_new_entry", "opened"),
        Input("modal_masterdata", "opened"),
        prevent_initial_call=False  # fmt: skip
    )

    @app.callback(
        Output("main_table", "filterModel"),
        Output("main_table", "selectedRows"),
        Input("eventlistener_scan", "n_events"),
        State("eventlistener_scan", "event"),
        State("modal_new_entry", "opened"),
        State("modal_masterdata", "opened"),
    )
    def handle_scan(
        n_events: int | None,
        event: ScanEvent,
        is_new_entry_open: bool,
        is_masterdata_open: bool,
    ) -> tuple[dict[str, dict[str, str]], list[dict[str, str]]]:
        """Search for the string that ``eventlistener_scan`` returns after firing and select the first available entry.

        Args:
            n_events (int | None): dummy input to trigger the callback when ``eventlistener_scan`` fires
            event (ScanEvent): event from the scanner containing the scanned code
            is_new_entry_open (bool): if the modal for creating new entries ``modal_new_entry`` is open
            is_masterdata_open (bool): if the modal for editing masterdata ``modal_masterdata`` is open

        Raises:
            PreventUpdate: in case the ``n_events`` triggers the callback but doesn't contain an event or details to it, or the modal for new entries or masterdata is open

        Returns:
            tuple[dict[str, dict[str, str]], list[dict[str, str]]]: _description_
        """

        if (
            not event
            or not event.get("detail")
            or is_new_entry_open
            or is_masterdata_open
        ):
            raise PreventUpdate

        barcode = event.get("detail").get("scanCode")
        filter = {
            "barcode": {
                "filterType": "text",
                "type": "contains",
                "filter": barcode,
            }
        }
        return filter, [{"barcode": barcode}]

    # Reset all filters from main_table when the Filter button is pressed
    @app.callback(
        Output("main_table", "filterModel", allow_duplicate=True),
        Output("btn_reset_filter", "disabled"),
        Input("btn_reset_filter", "n_clicks"),
        Input("main_table", "filterModel"),
    )
    def reset_filter(
        n_clicks: int, filter_model: dict
    ) -> tuple[dict | NoUpdate, bool] | None:
        """Reset all filters from the main table when the filter button is clicked and disable the button afterwards.
        Also toggle the filter button in case a filter is typed or cleared in the main table.

        Args:
            n_clicks (int): dummy input to trigger the callback with ``btn_reset_filter``
            filter_model (dict): filter model of the main table ``main_table``

        Returns:
            tuple[dict | NoUpdate, bool] | None: 2 Outputs: Returns the filterModel to ``main_table`` and sets ``disabled`` for ``btn_reset_filter``
        """

        if ctx.triggered_id == "btn_reset_filter":
            return {}, True
        elif ctx.triggered_id == "main_table":
            if len(filter_model) == 0:
                return no_update, True
            else:
                return no_update, False

    @app.callback(
        Output("modal_popover_database_search", "opened"),
        Output("popover_database_search", "opened"),
        Input("btn_confirm_database_search", "n_clicks"),
        Input("modal_btn_confirm_database_search", "n_clicks"),
        State("input_database_search", "value"),
        State("modal_input_database_search", "value"),
    )
    def update_entry_from_database_search(
        n_clicks: int, n_clicks_modal: int, value: str, value_modal: str
    ) -> tuple[bool | NoUpdate, bool | NoUpdate]:
        """When searching the database to apply information from an old entry or from GESTIS, fill the new or existing entry with the information and toggle the search popover.

        Args:
            n_clicks (int): dummy input to trigger the callback when clicking ``btn_confirm_database_search``
            n_clicks_modal (int): dummy input to trigger the callback when clicking ``modal_btn_confirm_database_search``
            value (str): value from the search input ``input_database_search`` in an existing entry
            value_modal (str): value from the search input ``modal_input_database_search`` in a new entry

        Returns:
            tuple[bool | NoUpdate, bool | NoUpdate]: closes the respective popover, depending on the button clicked
        """

        modal_prefix = ""

        if ctx.triggered_id == "modal_btn_confirm_database_search":
            modal_prefix = "modal_"
            existing_data = functions.get_existing_data(value_modal)
        else:
            existing_data = functions.get_existing_data(value)

        def set_field(
            key: str,
            field: str,
            data: dict = existing_data,
            modal_prefix: str = modal_prefix,
        ):
            """Updates the value of ``field`` corresponding to the value of ``key`` in ``data``"""

            if i := data.get(key):
                if i != "None":
                    set_props(modal_prefix + field, {"value": i})

        set_field("cas", "input_cas")
        set_field("name", "input_name")
        set_field("formular", "input_formular")
        set_field("room_id", "input_room")
        set_field("supplier_id", "input_supplier")
        set_field("unit_id", "input_unit")
        set_field("purchasedate", "input_purchasedate")
        set_field("manufacturer_id", "input_manufacturer")
        set_field("purity", "input_purity")
        set_field("concentration", "input_concentration")
        set_field("solvent", "input_solvent")
        set_field("molarmass", "input_molarmass")
        set_field("zvg", "input_zvg")

        if ctx.triggered_id == "modal_btn_confirm_database_search":
            return False, no_update
        else:
            return no_update, False

    @app.callback(
        Output("input_database_search", "value"),
        Output("modal_input_database_search", "value"),
        Input("popover_database_search", "opened"),
        Input("modal_popover_database_search", "opened"),
    )
    def reset_database_search(
        opened: bool, modal_opened: bool
    ) -> tuple[None | NoUpdate, None | NoUpdate]:
        """Set the input of the respective database search selector to ``None`` when it gets opened

        Args:
            opened (bool): dummy input to fire the callback when ``popover_database_search`` gets opened
            modal_opened (bool): dummy input to fire the callback when ``modal_popover_database_search`` gets opened

        Returns:
            tuple[None | NoUpdate, None | NoUpdate]: returns ``None`` to the respective input ``input_database_search`` or ``modal_input_database_search``
        """

        if ctx.triggered_id == "popover_database_search":
            return None, no_update
        else:
            return no_update, None

    @app.callback(
        Input("btn_purchasedate_today", "n_clicks"),
        Input("modal_btn_purchasedate_today", "n_clicks"),
        Input("btn_lastchecked_today", "n_clicks"),
        Input("modal_btn_lastchecked_today", "n_clicks"),
    )
    def set_datepicker_to_today(
        n_clicks_purchasedate_today: int,
        n_clicks_modal_purchasedate_today: int,
        n_clicks_lastchecked_today: int,
        n_clicks_modal_lastchecked_today: int,
    ) -> None:
        """Set the date to today in the ``DateInput`` components when their "today" button is clicked

        Args:
            n_clicks_purchasedate_today (int): dummy input to trigger the callback when ``btn_purchasedate_today`` is clicked
            n_clicks_modal_purchasedate_today (int): dummy input to trigger the callback when ``modal_btn_purchasedate_today`` is clicked
            n_clicks_lastchecked_today (int): dummy input to trigger the callback when ``btn_lastchecked_today`` is clicked
            n_clicks_modal_lastchecked_today (int): dummy input to trigger the callback when ``modal_btn_lastchecked_today`` is clicked
        """

        # Get all input ids from the callback inputs
        input_ids = [i["id"] for i in ctx.inputs_list]

        # Make some id manipulation to adress the correct input field, e.g. input_purchasedate or modal_input_purchasedate
        for id in input_ids:
            if ctx.triggered_id == id and isinstance(ctx.triggered_id, str):
                if "modal_" in ctx.triggered_id:
                    set_props(
                        id.removesuffix("_today").replace("btn_", "input_"),
                        {"value": TODAY},
                    )
                else:
                    set_props(
                        "input_" + id.removesuffix("_today").replace("btn_", ""),
                        {"value": TODAY},
                    )

    @app.callback(
        Output("cache_settings", "data", allow_duplicate=True),
        State("cache_settings", "data"),
        prevent_initial_call=False,
    )
    def init_settings_cache(settings_cache_json: str | None) -> str | NoUpdate:
        """Initialize the settings cache with default values if it not yet exists in the browser

        Args:
            settings_cache_json (str): the cache used for the settings

        Returns:
            str | NoUpdate: the settings saved in ``DEFAULT_SETTINGS`` as json
        """

        if settings_cache_json == None:
            return json.dumps(DEFAULT_SETTINGS)
        else:
            return no_update

    @app.callback(
        Output("modal_settings", "opened"),
        Input("btn_open_settings", "n_clicks"),
        Input("settings_btn_cancel", "n_clicks"),
        State("modal_settings", "opened"),
        State("cache_settings", "data"),
    )
    def open_modal_settings(
        n_clicks_open: int,
        n_clicks_cancel: int,
        is_open: bool,
        cache_settings_json: str,
    ) -> bool:
        """Open and close the settings modal ``modal_settings`` and set the settings to the values of the cache

        Args:
            n_clicks_open (int): dummy input to trigger the callback when ``btn_open_settings`` is clicked
            n_clicks_cancel (int): dummy input to trigger the callback when ``settings_btn_cancel`` is clicked
            is_open (bool): if the settings modal ``modal_settings`` is open
            cache_settings_json (str): the cache used for the settings

        Returns:
            bool: state of the ``opened`` attribute of ``modal_settings``
        """

        if ctx.triggered_id == "settings_btn_cancel":
            return not is_open

        cache_settings = json.loads(cache_settings_json)

        for key, value in cache_settings.items():
            set_props(key, {"value": value})
        return not is_open

    @app.callback(
        Output("cache_settings", "data", allow_duplicate=True),
        Output("modal_settings", "opened", allow_duplicate=True),
        Output("notifications", "sendNotifications", allow_duplicate=True),
        inputs=dict(
            n_clicks_save=Input("settings_btn_save", "n_clicks"),
            n_clicks_reset=Input("settings_btn_reset", "n_clicks"),
            settings_cache_json=State("cache_settings", "data"),
            # NOTE - Every Setting needs to be explicitly named here to be automatically recognized by the function.
            # The name of the variable doesn't matter, but the id musthave the same structure as in default_settings.json.
            settings=dict(
                datechange=State("settings_select_set_date_automatically", "value"),
                backup_frequence=State("settings_select_backup_frequency", "value"),
                backup_frequency_minutes=State(
                    "settings_input_backup_frequency", "value"
                ),
            ),
        ),
    )
    def save_settings(
        n_clicks_save: int,
        n_clicks_reset: int,
        settings_cache_json: str,
        settings: dict[str, str | int],
    ) -> tuple:
        """Save the settings to the browser cache

        Args:
            n_clicks_save (int): dummy input to trigger the callback when ``settings_btn_save`` is clicked
            n_clicks_reset (int): dummy input to trigger the callback when ``settings_btn_reset`` is clicked
            settings_cache_json (str): cache used for the settings
            settings (dict[str, str  |  int]): the value of all settings

        Returns:
            tuple: 3 Outputs
        """

        settings_cache = json.loads(settings_cache_json)

        # Create settings dict by looking at the callback inputs
        if isinstance(ctx.args_grouping, dict):
            settings = {
                i["id"]: i["value"] for i in ctx.args_grouping["settings"].values()
            }

        # When "reset" is clicked, go through each change and reset the setting to its previous or default value
        if ctx.triggered_id == "settings_btn_reset":
            for key in settings.keys():
                set_props(
                    "einstellung_" + key,
                    {"value": settings_cache.get(key, DEFAULT_SETTINGS[key])},
                )
            return no_update, no_update, no_update

        settings_cache.update(settings)

        messages = [
            dict(
                title="Gespeichert!",
                id=str(uuid.uuid4()),
                action="show",
                icon=DashIconify(
                    color="black",
                    height=24,
                    icon=icons.check,
                ),
                bg="green.3",
                color="green.3",
            )
        ]

        return json.dumps(settings_cache), False, messages

    @app.callback(
        Output("settings_wrapper_input_backup_frequency", "display"),
        Input("settings_select_backup_frequency", "value"),
    )
    def add_frequency_input(
        value_frequency: str,
    ) -> str:
        """Set the ``display`` property of ``settings_wrapper_input_backup_frequency``  to either ``"flex"`` or ``"None"``

        Args:
            value_frequency (str): select component ``settings_select_backup_frequency`` to trigger the calback. When set to ``"interval"``, the function returns ``"flex"``

        Returns:
            str: ``"flex"`` to display the input field, ``"None"`` to hide it"
        """

        if value_frequency == "interval":
            return "flex"
        else:
            return "None"

    @app.callback(
        Output("notifications", "sendNotifications", allow_duplicate=True),
        Input("cache_settings", "data"),
        Input("interval_backup_frequency", "n_intervals"),
        prevent_initial_call=False,
    )
    def manage_automatic_backup(
        cache_settings_json: str | None, n_intervals: int | None
    ) -> list[dict] | None:
        """Manage the logic for automatic backups.

        Args:
            cache_settings_json (str | None): cache ``cache_settings`` used for the settings
            n_intervals (int | None): dummy input to trigger the callback. Sent automatically by a set frequency from ``interval_backup_frequency``

        Raises:
            PreventUpdate: in case ``cache_settings`` is empty

        Returns:
            list[dict] | None: Gives out a notification to ``sendNotifications`` property of ``notifications``
        """

        if cache_settings_json != None:
            cache_settings = json.loads(cache_settings_json)
        else:
            raise PreventUpdate

        messages = [
            dict(
                title=i18n.get("Created backup!"),
                id=str(uuid.uuid4()),
                action="show",
                icon=DashIconify(
                    color="black",
                    height=24,
                    icon=icons.check,
                ),
                bg="gray.3",
                color="gray.3",
            )
        ]

        # The callback will fire on every (re)load of the page because of prevent_initial_call = False
        if cache_settings.get("settings_select_backup_frequency") == "open":
            functions.backup_db()
            return messages
        elif (
            cache_settings.get("settings_select_backup_frequency") == "interval"
            and ctx.triggered_id == "interval_backup_frequency"
        ):
            functions.backup_db()
            return messages

    @app.callback(
        Output("interval_backup_frequency", "disabled"),
        Output("interval_backup_frequency", "interval"),
        Input("cache_settings", "data"),
        prevent_initial_call=False,
    )
    def manage_interval_backup_timer(
        cache_settings_json: str | None,
    ) -> tuple[bool, int | NoUpdate]:
        """Starts and stops the time for interval-based backups

        Args:
            cache_settings_json (str | None): cache ``cache_settings`` used for the settings

        Raises:
            PreventUpdate: in case ``cache_settings`` is empty

        Returns:
            tuple[bool, int | NoUpdate]: enable or disable the interval component and set the interval in milliseconds
        """

        if cache_settings_json != None:
            cache_settings = json.loads(cache_settings_json)
        else:
            raise PreventUpdate

        frequency_ms = cache_settings.get("settings_input_backup_frequency") * 60 * 1000

        if cache_settings.get("settings_select_backup_frequency") == "interval":
            return False, frequency_ms
        else:
            return True, no_update

    @app.callback(
        Output("settings_download_export_database", "data"),
        Output("modal_confirm_backup", "opened"),
        Output("cache_current_database", "data"),
        Output("settings_btn_import_database", "contents"),
        Input("settings_btn_export_database", "n_clicks"),
        Input("settings_btn_create_database", "n_clicks"),
        Input("settings_btn_import_database", "contents"),
    )
    def database_tools(
        n_clicks_export: int, n_clicks_new: int, import_data: str | None
    ) -> tuple | None:
        """Controls the logic of the buttons in the settings for importing, exporting and creating a database

        Args:
            n_clicks_export (int): dummy input to trigger the callback when ``settings_btn_export_database`` is clicked
            n_clicks_new (int): dummy input to trigger the callback when ``settings_btn_create_database`` is clicked
            import_data (str | None): the uploaded file encoded in base64

        Returns:
            tuple: 4 Outputs
        """
        db = Path(f"current.sqlite")

        # Returns the currently opened database to the download component
        if ctx.triggered_id == "settings_btn_export_database":
            return (
                dcc.send_file(db),
                no_update,
                no_update,
                no_update,
            )

        if ctx.triggered_id == "settings_btn_import_database" and import_data:
            # Cut of the type description when importing the table.
            _, content = import_data.split(",")

            # If a database is currently loaded, open a modal to let the use confirm the import and put the current database into the cache
            if db.exists():
                return (
                    no_update,
                    True,
                    json.dumps(
                        {
                            "mode": "import",
                            "content": content,
                        }
                    ),
                    None,
                )
            # Otherwise create a new one and write the imported file directly to it
            else:
                Path.touch(db, exist_ok=False)

            # The content is encoded in base64, so it needs to be decoded
            # Write the uploaded content to the file
            db.write_bytes(base64.b64decode(content))

            # The last "None" is important to reset the upload component
            return (
                no_update,
                no_update,
                no_update,
                None,
            )

        if ctx.triggered_id == "settings_btn_create_database":
            if Path.exists(db):
                return (
                    no_update,
                    True,
                    json.dumps(
                        {
                            "mode": "new",
                            "content": None,
                        }
                    ),
                    None,
                )
            else:
                functions.init_app(LANG)

            return no_update, no_update, no_update, None

    @app.callback(
        Output("modal_confirm_backup", "opened", allow_duplicate=True),
        Output("cache_current_database", "data", allow_duplicate=True),
        Output("main_table", "rowData", allow_duplicate=True),
        Input("backup_btn_yes", "n_clicks"),
        Input("backup_btn_no", "n_clicks"),
        Input("backup_btn_cancel", "n_clicks"),
        State("cache_current_database", "data"),
    )
    def backup_db_on_import(
        n_clicks_yes: int,
        n_clicks_no: int,
        n_clicks_cancel: int,
        cache_current_database_json: str,
    ) -> tuple:
        """Controls the buttons of the modal ``modal_confirm_backup`` to confirm importing or creating a new database

        Args:
            n_clicks_yes (int): dummy input to trigger the callback when ``backup_btn_yes`` is clicked
            n_clicks_no (int): dummy input to trigger the callback when ``backup_btn_no`` is clicked
            n_clicks_cancel (int): dummy input to trigger the callback when ``backup_btn_cancel`` is clicked
            cache_current_database_json (str): the currently used database stored in cache ``cache_current_database``

        Returns:
            tuple: 3 Outputs
        """

        cache_current_database = json.loads(cache_current_database_json)
        mode = cache_current_database.get("mode")
        content_encoded = cache_current_database.get("content")

        if mode == "import":
            content = base64.b64decode(content_encoded)
        else:
            content = None

        db = Path(f"current.sqlite")

        if ctx.triggered_id == "backup_btn_yes":
            functions.backup_db()
            db.unlink()
            functions.init_app(LANG)

            if mode == "import" and content != None:
                db.write_bytes(content)

        elif ctx.triggered_id == "backup_btn_no":
            db.unlink()
            functions.init_app(LANG)

            if mode == "import" and content != None:
                db.write_bytes(content)

        elif ctx.triggered_id == "backup_btn_cancel":
            pass

        # Delete the saved cache to not use unnecessary space. Also renew the table, so that the new content is shown instantly.
        return (
            False,
            json.dumps(""),
            functions.get_main_table().to_dict("records"),
        )

    @app.callback(
        Output("modal_linechart_amount", "opened"),
        Output("chart_amount", "data"),
        Input("wrapper_sparkline_amount", "n_clicks"),
        State("modal_linechart_amount", "opened"),
        State("main_table", "selectedRows"),
    )
    def open_amount_chart(
        n_clicks: int, is_open: bool, selected_rows: list[dict]
    ) -> tuple[Literal[True], list[dict]]:
        """Open the modal to the amount chart

        Args:
            n_clicks (int): dummy input to trigger the callback when ``wrapper_sparkline_amount`` is clicked
            is_open (bool): if the modal ``modal_linechart_amount`` is open
            selected_rows (list[dict]): selected rows in the main table

        Returns:
            tuple[Literal[True], list[dict]]: Sets the property ``opened`` to ``True`` and outputs the data for the amount chart
        """

        barcode = selected_rows[0].get("barcode", "")
        data = functions.get_amount_chart_data(barcode)
        return True, data

    @app.callback(
        Input("eventlistener_keyboard", "n_events"),
        Input("eventlistener_keyboard", "event"),
        State("wrapper_entry", "hidden"),
        State("modal_new_entry", "opened"),
        State("modal_btn_save_entry", "disabled"),
        State("btn_create_new_entry", "disabled"),
    )
    def keyboard_event_manager(
        n_events: int | None,
        event: KeyboardEvent,
        is_right_window_hidden: bool,
        is_modal_new_entry_open: bool,
        is_btn_save__new_entry_disabled: bool,
        is_create_new_entry_disabled: bool,
    ) -> None:
        """Manages keyboard events, e.g. to open the modal to create new entries or quickly save edited entries.

        Args:
            n_events (int | None): dummy input to trigger the callback when ``eventlistener_keyboard`` fires an event
            event (KeyboardEvent): fired event from ``eventlistener_keyboard`` with information about the pressed keys
            is_right_window_hidden (bool): if the right window ``wrapper_entry`` to edit an existing entry is hidden
            is_modal_new_entry_open (bool): if the modal to create new entries ``modal_new_entry`` is open
            is_btn_save_new_entry_disabled (bool): if the button to save a new entry ``modal_btn_save_entry`` is disabled
            is_create_new_entry_disabled (bool): if the button ``btn_create_new_entry`` to open the modal to create new entries ``modal_new_entry`` is disabled
        """

        key = event.get("key")
        is_shift = event.get("shiftKey")
        is_metaKey = event.get("metaKey")
        is_ctrlKey = event.get("ctrlKey")
        tag_name = event.get("target.tagName")

        if is_shift:
            if key == "Enter":
                if not is_right_window_hidden and not is_modal_new_entry_open:
                    set_props("modal_confirm_save", {"opened": True})
                    return
                elif is_modal_new_entry_open and not is_btn_save__new_entry_disabled:
                    set_props("modal_confirm_save", {"opened": True})
                    return
            elif (
                is_metaKey
                and platform.system() == "Darwin"
                or is_ctrlKey
                and platform.system() == "Windows"
            ):
                if key.lower() == "e":
                    if (
                        tag_name != "INPUT"
                        and not is_modal_new_entry_open
                        and not is_create_new_entry_disabled
                    ):
                        patched_button = Patch()
                        patched_button["n_clicks"] += 1
                        set_props(
                            "btn_create_new_entry",
                            {"n_clicks": patched_button},
                        )

    @app.callback(
        Output("modal_confirm_save", "opened"),
        Input("save_btn_yes", "n_clicks"),
        Input("save_btn_cancel", "n_clicks"),
        State("modal_new_entry", "opened"),
    )
    def confirm_entry_save(
        n_clicks_yes: int,
        n_clicks_cancel: int,
        is_new_entry_open: bool,
    ) -> Literal[False]:
        """Controls the logic behind the modal ``modal_confirm_save`` to confirm a new or edited entry

        Args:
            n_clicks_yes (int): dummy input to trigger the callback when ``save_btn_yes`` is clicked
            n_clicks_cancel (int): dummy input to trigger the callback when ``save_btn_cancel`` is clicked
            is_new_entry_open (bool): if the modal to create a new entry ``modal_new_entry`` is open

        Returns:
            Literal[False]: close the modal ``modal_confirm_save``  to confirm the entry
        """

        patched_button = Patch()
        patched_button["n_clicks"] += 1

        if ctx.triggered_id == "save_btn_yes":
            if is_new_entry_open:
                set_props(
                    "modal_btn_save_entry",
                    {"n_clicks": patched_button},
                )
            elif not is_new_entry_open:
                set_props("btn_save_entry", {"n_clicks": patched_button})
        elif ctx.triggered_id == "save_btn_cancel":
            pass

        return False

    @app.callback(
        Output("input_name", "leftSection"),
        Output("btn_toggle_archive", "children"),
        Output("btn_toggle_archive", "variant"),
        Output("btn_create_new_entry", "disabled"),
        Output("main_table", "dashGridOptions"),
        Output("btn_archive_entry", "children"),
        Output("btn_archive_entry_tooltip", "label"),
        Output("btn_archive_entry", "rightSection"),
        Output("main_table", "rowData", allow_duplicate=True),
        Output("main_table", "selectedRows", allow_duplicate=True),
        Input("btn_toggle_archive", "n_clicks"),
        State("input_name", "leftSection"),
    )
    def open_archive(n_clicks: int, left_section: dict | None) -> tuple:
        """Control the logic of the archive button ``btn_toggle_archive``

        Args:
            n_clicks (int): dummy input to trigger the callback when ``btn_toggle_archive`` is clicked
            left_section (dict | None): left section of the button ``input_name``

        Returns:
            tuple: 10 Outputs
        """

        grid_dark = Patch()
        grid_light = Patch()

        grid_dark["theme"]["function"] = (
            "themeQuartz.withParams({fontFamily: 'Lexend',"
            "headerTextColor: '#fff',"
            "headerBackgroundColor: '#333',"
            "headerColumnResizeHandleColor: '#777',"
            "backgroundColor: '#222',"
            "foregroundColor: '#fff'})"
        )

        grid_light["theme"][
            "function"
        ] = "themeQuartz.withParams({fontFamily: 'Lexend'})"

        # The left section of the input field is a tell that the archive is not enabled.
        # Otherwise it displays the archive icon
        if not left_section:
            df = functions.get_main_table(is_archived=True)
            return (
                DashIconify(
                    icon=icons.archive,
                    height=24,
                ),
                DashIconify(
                    icon=icons.archiveClose,
                    height=24,
                ),
                "gradient",
                True,
                grid_dark,
                dmc.Text(i18n.get("Restore"), visibleFrom="xl"),
                i18n.get("Restore"),
                DashIconify(
                    icon=icons.unarchive,
                ),
                df.to_dict("records"),
                [{"barcode": ""}],
            )
        else:
            df = functions.get_main_table()
            return (
                None,
                DashIconify(
                    icon=icons.archive,
                    height=24,
                ),
                "filled",
                False,
                grid_light,
                dmc.Text(i18n.get("Archive"), visibleFrom="xl"),
                i18n.get("Archive"),
                DashIconify(
                    icon=icons.archive,
                ),
                df.to_dict("records"),
                [{"barcode": ""}],
            )

    @app.callback(
        Output("main_table", "rowData", allow_duplicate=True),
        Output("notifications", "sendNotifications", allow_duplicate=True),
        Input("btn_archive_entry", "n_clicks"),
        State("input_name", "leftSection"),
        State("main_table", "selectedRows"),
    )
    def transfer_to_archive(
        n_clicks: int, left_section: dict | None, selected_rows: list[dict]
    ) -> tuple:
        """Control the logic of the button ``btn_archive_entry`` to put an entry into or out of the archive

        Args:
            n_clicks (int): dummy input to trigger the callback when ``btn_archive_entry`` is clicked
            left_section (dict | None): left section of the button ``input_name``
            selected_rows (list[dict]): selected row in the main table

        Returns:
            tuple: 2 Outputs
        """

        barcode = selected_rows[0].get("barcode", "")

        # The icon of the name input is a sign that the archive is currently enabled
        # The button should then put the entry out of archive
        if left_section:
            functions.archive_row(barcode, False)
            df = functions.get_main_table(is_archived=True)
            message = [
                dict(
                    title=i18n.get("Restored"),
                    message=i18n.get(
                        "The entry ${barcode} was restored.",
                        values={"barcode": barcode},
                    ),
                    id=str(uuid.uuid4()),
                    action="show",
                    icon=DashIconify(
                        color="black",
                        height=24,
                        icon=icons.unarchive,
                    ),
                    bg="green.3",
                    color="green.3",
                )
            ]
        # With no icon in left section, it should archive entries instead
        else:
            functions.archive_row(barcode, True)
            df = functions.get_main_table()
            message = [
                dict(
                    title=i18n.get("Archived"),
                    message=i18n.get(
                        "The entry ${barcode} was archived.",
                        values={"barcode": barcode},
                    ),
                    id=str(uuid.uuid4()),
                    action="show",
                    icon=DashIconify(
                        color="black",
                        height=24,
                        icon=icons.archive,
                    ),
                    bg="green.3",
                    color="green.3",
                )
            ]

        return df.to_dict("records"), message

    @app.callback(
        Output("btn_open_gestis", "disabled"),
        Output("anchor_open_gestis", "href"),
        Input("input_zvg", "value"),
    )
    def toggle_gestis_button(value: str) -> tuple:
        """Disable or enable the gestis button ``btn_open_gestis`` depending if the ZVG field ``input_zvg`` is empty or not

        Args:
            value (str): input to trigger the callback when the value of the ZVG field ``input_zvg`` changes

        Returns:
            tuple: 2 Outputs
        """
        if value == "":
            return True, ""
        else:
            value = value.rjust(6, "0")
            return False, f"https://gestis.dguv.de/data?name={value}"
