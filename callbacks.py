from dash_iconify import DashIconify
from dash import (
    Input,
    Output,
    State,
    Patch,
    ctx,
    no_update,
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

import icons
from i18n import i18n
from default_values import DEFAULT_SETTINGS, TODAY, LANG


def get_callbacks(app):

    # Initialize the main table with fresh data from the database.
    # The input of wrapper_main is just a dummy. The callback gets fired everytime wrapper_main is initialized on the website by default.
    @app.callback(
        Output("main_table", "rowData"),
        Input("wrapper_main", "children"),
        prevent_initial_call=False,
    )
    def init_mainGrid(children):
        return functions.get_main_table().to_dict("records")

    # Callback das jedes Feld aktualisiert, sobald man eine neue Zeile in der Tabelle auswählt
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
    def update_fields(rows):
        patched_input = Patch()
        patched_input["display"] = "None"
        # Standardobjekt, wenn nichts angezeigt werden kann oder soll
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
            patched_input,  # Blende "wrapper_entry" aus
            "flex",  # Blende den Platzhalter ein
            True,
            no_update,
        )
        if not rows:  # Wenn nichts ausgewählt ist
            return nothing_selected
        barcode = rows[0].get("barcode", "")
        # Wenn der Barcode nicht in der Tabelle hinterlegt ist, dann zeige den Platzhalter an und setze die anderen Werte zurück
        if functions.select_value(barcode, "barcode", functions.Inventory) == "":
            return nothing_selected

        # Blende die Sparkline neben der Füllmenge standardmäßig aus
        füllmenge_hidden = True
        füllmenge_data = []

        # Extrahiere die letzte Füllmenge aus dem JSON-Array aller gespeicherten Füllmengen
        füllmenge_raw = functions.select_value(barcode, "amount", functions.Inventory)
        if len(füllmenge_raw or []) != 0 and füllmenge_raw:
            füllmenge = json.loads(füllmenge_raw)
            füllmenge_last_entry = füllmenge[-1][1]
            if len(füllmenge) > 1:
                füllmenge_hidden = False  # Blende die Sparkline ein, wenn mehr als 1 Eintrag vorhanden ist
                füllmenge_data = [i[1] for i in füllmenge]
        else:
            füllmenge_last_entry = füllmenge_raw

        patched_input["display"] = "flex"
        return (
            barcode,
            füllmenge_last_entry,
            *[  # Gebe für jedes Feld den entsprechenden Wert aus der Inventartabelle zurück
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
            füllmenge_hidden,
            füllmenge_data,
        )

    # Sobald der Speicherbutton gedrückt wird, aktualisiere die Werte in der sichtbaren Tabelle wie auch in der Datenbank
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
    def save_data(
        n_clicks,
        name,
        barcode,
        amount,
        purchasedate,
        manufacturer_id,
        supplier_id,
        room_id,
        purity,
        concentration,
        solvent,
        cas,
        molarmass,
        formular,
        unit_id,
        lastchecked,
        zvg,
        einstellungen_cache,
    ):
        # Falls die Felder leer sind trage 0 ein, was dem leeren Wert in der SQL-Tabelle entspricht
        if manufacturer_id == None or "":
            manufacturer_id = 0
        if supplier_id == None or "":
            supplier_id = 0
        if room_id == None or "":
            room_id = 0
        if unit_id == None or "":
            unit_id = 0

        messages = [
            dict(  # ...und gebe eine Notifikation heraus
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
        if "," in str(amount):
            amount = amount.replace(",", ".")
            messages.append(
                dict(  # ...und gebe eine Notifikation heraus
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
        if "," in str(molarmass):
            molarmass = molarmass.replace(",", ".")
            messages.append(
                dict(  # ...und gebe eine Notifikation heraus
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
        # Überprüfe, ob die Einstellung aktiviert ist, bei der das Datum beim Speichern automatisch auf das heutige gesetzt wird.
        # Wenn ja, dann hänge eine Nachricht an, dass das geschehen ist und überschreibe das vorherige Datum mit heute.
        einstellungen_cache = json.loads(einstellungen_cache)
        if (
            einstellungen_cache.get("settings_select_set_date_automatically")
            == "change"
            or einstellungen_cache.get("settings_select_set_date_automatically")
            == "createchange"
        ) and lastchecked != TODAY:
            lastchecked = TODAY
            set_props("input_lastchecked", {"value": lastchecked})
            messages.append(
                dict(  # ...und gebe eine Notifikation heraus
                    title="Achtung!",
                    message="Das Prüfdatum des Eintrages wurde auf den heutigen Tag gesetzt.",
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

        # Lade die historischen Einträge der Füllmenge und ergänze die neu eingetragene Füllmenge, falls sie nicht schon im Array unter diesem Datum vorhanden ist.
        füllmenge_history, füllmenge_data = functions.save_füllmenge(
            barcode,
            lastchecked,
            amount,
        )

        füllmenge_hidden = True

        if len(füllmenge_data) > 1:
            füllmenge_hidden = False

        # Trage alle Werte in der Datenbank ein
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
                füllmenge_history,
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

        return (df.to_dict("records"), messages, füllmenge_hidden, füllmenge_data)

    # Kontrolliert die Logik des "Eintrag Löschen" Modals
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
        n_clicks_löschen,
        n_clicks_abbrechen,
        n_clicks_ja,
        rows,
    ):
        if ctx.triggered_id == "btn_delete_entry":
            return no_update, no_update, no_update, True
        elif ctx.triggered_id == "delete_btn_cancel":
            return no_update, no_update, no_update, False
        elif ctx.triggered_id == "delete_btn_yes":
            barcode = rows[0].get("barcode", "")
            functions.delete_entry(barcode, functions.Inventory)
            global df  # Greife auf den globalen Dataframe zurück, damit die Tabelle auch nach Pagerefresh oder auf einem anderen Computer geändert ist
            df = functions.get_main_table()
            return (
                df.to_dict("records"),
                [
                    dict(  # ...und gebe eine Notifikation heraus
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

    # Öffne bzw. schließe das Fenster, in dem ein neuer Eintrag hinzugefügt werden kann und setze alle Felder zurück
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
        State("modal_new_entry", "opened"),
        State("modal_masterdata", "opened"),
    )
    def openModalNeuerEintrag(
        n_clicks1,
        n_clicks2,
        n_clicks3,
        einstellungen_cache,
        opened,
        n_events,
        event,
        isNeuerEintragOpen,
        isStammdatenOpen,
    ):
        einstellungen_cache = json.loads(einstellungen_cache)
        patched_n_blur = no_update

        if (
            einstellungen_cache.get("settings_select_set_date_automatically")
            == "create"
            or einstellungen_cache.get("settings_select_set_date_automatically")
            == "createchange"
        ):
            input_geprüft = TODAY
        else:
            input_geprüft = ""

        if ctx.triggered_id == "eventlistener_scan":
            if (
                not event
                or not event.get("detail")
                or isNeuerEintragOpen
                or isStammdatenOpen
            ):
                raise PreventUpdate
            barcode = event.get("detail").get("scanCode")
            patched_n_blur = Patch()
            patched_n_blur += 1

            if functions.select_value(barcode, "barcode", functions.Inventory) == "":
                return (
                    not opened,
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
                    input_geprüft,
                    patched_n_blur,
                )
            else:
                raise PreventUpdate

        return (
            not opened,
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
            input_geprüft,
            patched_n_blur,
        )

    # Gebe einen Fehler zurück, wenn der Barcode bereits vergeben ist
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
    def is_barcode_used(n_blur, barcode):
        selected = functions.select_value(barcode, "barcode", functions.Inventory)
        if "" == barcode:
            return ("Barcode darf nicht leer sein", True)
        elif selected == barcode:
            return ("Barcode ist bereits vergeben", True)
        else:
            return (None, False)

    # Speichere den neuen Eintrag
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
    def save_new_data(
        n_clicks,
        name,
        barcode,
        amount,
        purchasedate,
        manufacturer_id,
        supplier_id,
        room_id,
        purity,
        concentration,
        solvent,
        cas,
        molarmass,
        formular,
        unit_id,
        lastchecked,
        zvg,
    ):
        # Falls die ID-Felder leer sind trage 0 ein, was dem "Nicht ausgewählt" in der SQL-Tabelle entspricht
        if manufacturer_id == None or "":
            manufacturer_id = 0
        if supplier_id == None or "":
            supplier_id = 0
        if room_id == None or "":
            room_id = 0
        if unit_id == None or "":
            unit_id = 0
        # Trage bei den Reelen Zahlen None ein, falls sie leer gelassen werden. "" gibt als String andernfalls einen Fehler.
        if amount == "":
            amount = None
        if molarmass == "":
            molarmass = None

        messages = [
            dict(  # ...und gebe eine Notifikation heraus
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

        if "," in str(amount) and amount:
            amount = amount.replace(",", ".")
            messages.append(
                dict(  # ...und gebe eine Notifikation heraus
                    title="Achtung!",
                    message='"," in Füllmenge wurde durch "." ersetzt.',
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
                dict(  # ...und gebe eine Notifikation heraus
                    title="Achtung!",
                    message='"," in molarer Masse wurde durch "." ersetzt.',
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
        # Lade die historischen Einträge der Füllmenge und ergänze die neu eingetragene Füllmenge, falls sie nicht schon im Array unter diesem Datum vorhanden ist.
        füllmenge_history, füllmenge_data = functions.save_füllmenge(
            barcode,
            lastchecked,
            amount,
        )
        # Trage alle Werte in der Datenbank ein
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
                füllmenge_history,
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

        global df  # Greife auf den globalen Dataframe zurück, damit die Tabelle auch nach Pagerefresh oder auf einem anderen Computer geändert ist
        df = functions.get_main_table()
        return (
            df.to_dict("records"),
            messages,
        )

    # Open and close the modal, in which the master data gets edited
    # Initialize the master table with the last value of the selector
    # Reset the master table, when "Reset changes" gets clicked
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
        n_clicksModal: int | None,
        n_clicksZurücksetzen: int | None,
        n_clicksAbbrechen: int | None,
        selector: str,
        opened: bool,
    ):
        if ctx.triggered_id == "btn_masterdata_cancel":
            return (
                not opened,
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
        columnDefs = [
            {
                "field": i,
                "sortable": True,
                "editable": True,
                "headerName": getattr(
                    functions.stammdatenTables[selector], i.lower()
                ).doc,
            }
            for i in headings
        ]

        # Let the last column take up the remaining space
        columnDefs[-1].update({"flex": True})

        # Set the first column as not-editable
        columnDefs[0].update({"editable": False})

        # Use the names of the available buildings in a select component
        # instead of only the building ID
        if columnDefs[1].get("field") == "building_id":
            label_value = functions.generateSelectData(
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
            columnDefs[1].update(
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
                columnDefs,
                df.to_dict("records"),
                json.dumps(cache),
                True,
                True,
                True,
            )

        if ctx.triggered_id == "select_masterdata_tables":
            return (
                no_update,
                columnDefs,
                df.to_dict("records"),
                json.dumps(cache),
                True,
                True,
                True,
            )

        return (
            not opened,
            columnDefs,
            df.to_dict("records"),
            json.dumps(cache),
            no_update,
            True,
            True,
        )

    # Delete all notifications in the the queue and currently displayed when the modal is opened or closed
    @app.callback(
        Output("notifications", "clean", allow_duplicate=True),
        Input("modal_masterdata", "opened"),
    )
    def cleanNotificationContainer(opened):
        return True

    # Füge mit den Buttons Zeilen zur Stammdatentabelle hinzu oder lösche sie
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
    def addRemoveLine(
        n_clicks_hinzufügen, n_clicks_löschen, rowData, columnDefs, cache, selectedRows
    ):
        if selectedRows:
            selectedRow = selectedRows[0]
        cache = json.loads(cache)
        firstColumnName = columnDefs[0].get("field")
        firstColumnEntries = [row.get(firstColumnName) for row in rowData]
        firstColumnEntries.sort()

        # Finde eine ungenutzte ID
        unusedID = None

        if firstColumnEntries == []:
            unusedID = 1
        else:
            for i in range(len(firstColumnEntries) - 1):
                diff = firstColumnEntries[i + 1] - firstColumnEntries[i]
                if diff > 1:
                    unusedID = firstColumnEntries[i] + 1

        if unusedID == None:
            unusedID = firstColumnEntries[-1] + 1

        # Wenn auf "Zeile hinzufügen" gedrückt wird:
        if ctx.triggered_id == "btn_masterdata_add_row":
            # Überprüfe, ob die Reihe schonmal editiert wurde und daher als dict hinterlegt ist, sonst wirft .get() einen Fehler, weile dort kein dict existiert.
            if isinstance(cache.get(str(unusedID)), dict):
                if "Delete" in cache.get(str(unusedID)).get("op"):
                    cache.update({str(unusedID): {"op": "Update"}})
            else:
                cache.update({str(unusedID): {"op": "Insert"}})
            return (
                {"add": [{firstColumnName: unusedID}]},
                no_update,
                json.dumps(cache),
                False,
                False,
            )

        firstColumnId = str(selectedRow.get(firstColumnName))

        # Wenn auf "Zeile löschen" gedrückt wird
        if ctx.triggered_id == "btn_masterdata_delete_row":
            # Überprüfe wieder, ob die Zeile bereits im Cache liegt
            if isinstance(cache.get(str(selectedRow.get(firstColumnName))), dict):
                # Lösche die Zeile aus dem Cache, wenn sie mit inserted eingefügt wurde
                if not "Update" == cache.get(firstColumnId).get("op"):
                    cache.pop(firstColumnId)
                    if cache == {}:
                        is_disabled = True
                    else:
                        is_disabled = False
                    return (
                        no_update,
                        True,
                        json.dumps(cache),
                        is_disabled,
                        is_disabled,
                    )

            # Liegt sie noch nicht mit "Insert" im Cache, so speichere sie mit "Delete" als Operation im Cache ab
            cache.update(
                {
                    firstColumnId: {
                        firstColumnName: firstColumnId,
                        "op": "Delete",
                    }
                }
            )
            return (no_update, True, json.dumps(cache), False, False)

    # Blende den Zeile löschen-Button aus, wenn die Zeile mit der ID 0 ausgewählt ist.
    @app.callback(
        Output("btn_masterdata_delete_row", "disabled", allow_duplicate=True),
        Input("masterdata_table", "selectedRows"),
        State("masterdata_table", "columnDefs"),
    )
    def toggleDeleteButton(selectedRows, columnDefs):
        if selectedRows:
            selectedRow = selectedRows[0]
        firstColumnName = columnDefs[0].get("field")
        selectedRowID = selectedRow.get(firstColumnName)

        if selectedRowID == 0:
            return True
        else:
            return False

    # Speichere die Zeilen im Cache ab, wenn ein Zeileneintrag geändert wird
    @app.callback(
        Output("cache_masterdata", "data", allow_duplicate=True),
        Output("btn_masterdata_reset", "disabled", allow_duplicate=True),
        Output("btn_masterdata_save", "disabled", allow_duplicate=True),
        Input("masterdata_table", "cellValueChanged"),
        State("cache_masterdata", "data"),
        State("masterdata_table", "columnDefs"),
    )
    def editLine(cellValue, cache, columnDefs):
        firstColumnName = columnDefs[0].get("field")
        cache = json.loads(cache)

        if isinstance(
            cache.get(str(cellValue[0].get("data").get(firstColumnName))), dict
        ):  # Überprüfe, ob die editierte Zeile schon im Cache liegt –> dann wurde sie bereits editiert
            previous_op = cache[str(cellValue[0].get("data").get(firstColumnName))].get(
                "op"
            )
            cache[str(cellValue[0].get("data").get(firstColumnName))] = cellValue[
                0
            ].get("data")
            cache[str(cellValue[0].get("data").get(firstColumnName))][
                "op"
            ] = previous_op

        else:
            cache.update(
                {
                    str(cellValue[0].get("data").get(firstColumnName)): cellValue[
                        0
                    ].get("data"),
                }
            )
            cache[str(cellValue[0].get("data").get(firstColumnName))]["op"] = "Update"
        if cache == {}:
            is_disabled = True
        else:
            is_disabled = False
        return json.dumps(cache), is_disabled, is_disabled

    # Speichere die geänderten Zeilen der Stammdatentabelle in der Datenbank ab.
    @app.callback(
        Output("cache_masterdata", "data", allow_duplicate=True),
        Output("notifications", "sendNotifications", allow_duplicate=True),
        Output("btn_masterdata_reset", "disabled", allow_duplicate=True),
        Output("btn_masterdata_save", "disabled", allow_duplicate=True),
        Input("btn_masterdata_save", "n_clicks"),
        State("select_masterdata_tables", "value"),
        State("cache_masterdata", "data"),
    )
    def saveData(n_clicks, selector, cache):
        cache = json.loads(cache)
        messages = []
        modify_cache = cache.copy()
        correctly_saved = set()
        for id, cached in cache.items():
            columns = []
            values = []
            for c, v in cached.items():
                if c != "op":
                    # Die Spalte "Gebäude_ID" bei Räumen enthält nicht die ID, sondern einen zusammengesetzten String aus ID und Wert. Extrahiere also vor dem Speichern die ID.
                    columns.append(c)
                    if c == "building_id":
                        try:
                            values.append(v.split(":")[0])
                        except:  # Bei den Gebäuden ist die Gebäude_ID eine gewöhnliche ID, also muss sie nicht vorher gesplitted werden.
                            values.append(v)
                    else:
                        values.append(v)
                if c == "op":
                    op = v

            # Falls ein Fehler passiert, hänge eine Nachricht an
            if len(columns) == 0:
                messages.append(
                    dict(  # ...und gebe eine Notifikation heraus
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
            if op == "Update":
                try:
                    functions.updateStammdaten(selector, columns, values)
                    modify_cache.pop(id)
                    correctly_saved.add(id)
                except Exception as e:
                    messages.append(
                        dict(  # ...und gebe eine Notifikation heraus
                            title=i18n.get(
                                "Error updating entry with ID ${id}", values={"id": id}
                            ),
                            message=functions.convertErrorToMessage(e),
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
                    functions.deleteStammdaten(selector, values)
                    modify_cache.pop(id)
                    correctly_saved.add(id)
                except Exception as e:
                    messages.append(
                        dict(  # ...und gebe eine Notifikation heraus
                            title=i18n.get(
                                "Error deleting entry with ID ${id}", values={"id": id}
                            ),
                            message=functions.convertErrorToMessage(e),
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
                    functions.insertStammdaten(selector, columns, values)
                    modify_cache.pop(id)
                    correctly_saved.add(id)
                except Exception as e:
                    messages.append(
                        dict(  # ...und gebe eine Notifikation heraus
                            title=i18n.get(
                                "Error inserting entry with ID ${id}", values={"id": id}
                            ),
                            message=functions.convertErrorToMessage(e),
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
                    dict(  # ...und gebe eine Notifikation heraus
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
        if modify_cache == {}:
            is_disabled = True
        else:
            is_disabled = False
        if len(correctly_saved) == 1:
            for (
                id
            ) in (
                correctly_saved
            ):  # For-Schleife zum Extrahieren des Elementes im Set – ist sonst nicht abrufbar
                messages.append(
                    dict(  # ...und gebe eine Notifikation heraus
                        title="Gespeichert!",
                        message=f"Der Eintrag mit ID {id} wurde korrekt gespeichert.",
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
        elif len(correctly_saved) > 1:
            str_id = ""
            for id in correctly_saved:
                str_id += f"{id}, "
            str_id = str_id.rstrip(", ")
            messages.append(
                dict(  # ...und gebe eine Notifikation heraus
                    title="Gespeichert!",
                    message=f"Die Einträge mit IDs {str_id} wurden korrekt gespeichert.",
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

    # Aktualisiere alle Select-Felder, die Daten aus der Datenbank anzeigen, nachdem die Datenbank modifiziert wurde. Dadurch werden keine veralteten Daten angezeigt.
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
    def updateLists(n_clicks_stammdaten, n_clicks_speichern):
        if ctx.triggered_id == "btn_masterdata_save":
            return (
                functions.generateSelectData_Namen(),
                functions.generateSelectData(
                    functions.Units,
                    ["unit_id", "unit"],
                ),
                functions.generateSelectData(
                    functions.Manufacturers, ["manufacturer_id", "manufacturer"]
                ),
                functions.generateSelectData(
                    functions.Suppliers, ["supplier_id", "supplier"]
                ),
                functions.generateSelectData_Räume(),
                functions.generateSelectData_Namen(),
                functions.generateSelectData(
                    functions.Units,
                    ["unit_id", "unit"],
                ),
                functions.generateSelectData(
                    functions.Manufacturers, ["manufacturer_id", "manufacturer"]
                ),
                functions.generateSelectData(
                    functions.Suppliers, ["supplier_id", "supplier"]
                ),
                functions.generateSelectData_Räume(),
            )
        else:
            return (
                functions.generateSelectData_Namen(),
                no_update,
                no_update,
                no_update,
                no_update,
                functions.generateSelectData_Namen(),
                no_update,
                no_update,
                no_update,
                no_update,
            )

    # Initialisiere den Scan-Script, der zwischen normalem Input und gescannten Input unterscheidet. Scanner soll als normale Tastatur funktionieren, wenn Stammdaten- oder "Neuer Eintrag"-Fenster geöffnet ist.
    clientside_callback(
        ClientsideFunction(namespace="helper", function_name="initScanner"),
        Output("eventlistener_scan", "id"),
        Input("eventlistener_scan", "id"),
        Input("modal_new_entry", "opened"),
        Input("modal_masterdata", "opened"),
        prevent_initial_call=False  # fmt: skip
    )

    # Search for the string that the eventlistener_scan returns after firing and select the first available entry
    @app.callback(
        Output("main_table", "filterModel"),
        Output("main_table", "selectedRows"),
        Input("eventlistener_scan", "n_events"),
        State("eventlistener_scan", "event"),
        State("modal_new_entry", "opened"),
        State("modal_masterdata", "opened"),
    )
    def handle_scan(n_events, event, isNeuerEintragOpen, isStammdatenOpen):
        if (
            not event
            or not event.get("detail")
            or isNeuerEintragOpen
            or isStammdatenOpen
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
    def resetFilter(n_clicks, filterModel):
        if ctx.triggered_id == "btn_reset_filter":
            return {}, True
        elif ctx.triggered_id == "main_table":
            if len(filterModel) == 0:
                return no_update, True
            else:
                return no_update, False

    # Fill a new or existing entry with the contents of the gestis database or another existing entry
    @app.callback(
        Output("modal_popover_database_search", "opened"),
        Output("popover_database_search", "opened"),
        Input("btn_confirm_database_search", "n_clicks"),
        Input("modal_btn_confirm_database_search", "n_clicks"),
        State("input_database_search", "value"),
        State("modal_input_database_search", "value"),
    )
    def updateFromExistingData(n_clicks, n_clicksModal, value, valueModal):
        modalPrefix = ""
        if ctx.triggered_id == "modal_btn_confirm_database_search":
            modalPrefix = "modal_"
            existingData = functions.getExistingData(valueModal)
        else:
            existingData = functions.getExistingData(value)

        def setField(
            key: str,
            field: str,
            data: dict = existingData,
            modalPrefix: str = modalPrefix,
        ):
            """Updates the value of ``field`` corresponding to the value of ``key`` in ``data``"""

            if i := data.get(key):
                if i != "None":
                    set_props(modalPrefix + field, {"value": i})

        setField("cas", "input_cas")
        setField("name", "input_name")
        setField("formular", "input_formular")
        setField("room_id", "input_room")
        setField("supplier_id", "input_supplier")
        setField("unit_id", "input_unit")
        setField("purchasedate", "input_purchasedate")
        setField("manufacturer_id", "input_manufacturer")
        setField("purity", "input_purity")
        setField("concentration", "input_concentration")
        setField("solvent", "input_solvent")
        setField("molarmass", "input_molarmass")
        setField("zvg", "input_zvg")

        if (
            ctx.triggered_id == "modal_btn_confirm_database_search"
        ):  # Schließe das Modal, wenn auf "Eintrag übernehmen" gedrückt wird
            return False, no_update
        else:
            return no_update, False

    # Set the input of the database search selector to a blank string when it gets opened
    @app.callback(
        Input("popover_database_search", "opened"),
        Input("modal_popover_database_search", "opened"),
    )
    def resetSelectFromDatabase(opened, modalOpened):
        if ctx.triggered_id == "popover_database_search":
            set_props("input_database_search", {"value": None})
        elif ctx.triggered_id == "modal_popover_database_search":
            set_props("modal_input_database_search", {"value": None})

    # Setze das Datum auf Heute bei den DateInput-Selektoren, wenn auf den "Heute"-Button gedrückt wird
    @app.callback(
        Input("btn_purchasedate_today", "n_clicks"),
        Input("modal_btn_purchasedate_today", "n_clicks"),
        Input("btn_lastchecked_today", "n_clicks"),
        Input("modal_btn_lastchecked_today", "n_clicks"),
    )
    def setDateToToday(
        n_clicks_kaufdatumHeute,
        n_clicks_modalKaufdatumHeute,
        n_clicks_geprüftHeute,
        n_clicks_modalGeprüftHeute,
    ):
        input_ids = [
            "btn_purchasedate_today",
            "modal_btn_purchasedate_today",
            "btn_lastchecked_today",
            "modal_btn_lastchecked_today",
        ]
        # Setzt den Output des Feldes auf das heutige Datum, wenn der Button vom Feld gedrückt wird.
        # Entferne dafür "-heute" hinter der ID, um auf das Feld und nicht den Button zu verweisen.
        for id in input_ids:
            if ctx.triggered_id == id:
                set_props(id.removesuffix("-heute"), {"value": TODAY})
        return

    # Öffne oder schließe das Einstellungsmenü
    @app.callback(
        Output("modal_settings", "opened"),
        Input("btn_open_settings", "n_clicks"),
        Input("settings_btn_cancel", "n_clicks"),
        State("modal_settings", "opened"),
        State("cache_settings", "data"),
    )
    def toggleSettings(n_clicks_Öffnen, n_clicks_Abbrechen, opened, cache):
        if ctx.triggered_id == "settings_btn_cancel":
            return not opened

        cache = json.loads(cache)

        for (
            key,
            value,
        ) in (
            cache.items()
        ):  # Falls die Einstellung im Cache ist, setze ihren Wert auf den gespeicherten Wert im Cache
            set_props(key, {"value": value})
        return not opened

    # Initialisiere das Cache mit den Einstellungen
    @app.callback(
        Output("cache_settings", "data", allow_duplicate=True),
        State("cache_settings", "data"),
        prevent_initial_call=False,
    )
    def init_settings(settings_cache):
        if settings_cache == None:
            return json.dumps(DEFAULT_SETTINGS)
        else:
            return no_update

    # Speichere die Daten der Einstellungen im Browser ab
    @app.callback(
        Output("cache_settings", "data", allow_duplicate=True),
        Output("modal_settings", "opened", allow_duplicate=True),
        Output("notifications", "sendNotifications", allow_duplicate=True),
        inputs=dict(
            n_clicks_speichern=Input("settings_btn_save", "n_clicks"),
            n_clicks_reset=Input("settings_btn_reset", "n_clicks"),
            settings_cache=State("cache_settings", "data"),
            settings=dict(
                datumsänderung=State("settings_select_set_date_automatically", "value"),
                backup_häufigkeit=State("settings_select_backup_frequency", "value"),
                backup_häufigkeit_minuten=State(
                    "settings_input_backup_frequency", "value"
                ),
            ),
        ),
    )
    def save_settings(
        n_clicks_speichern,
        n_clicks_reset,
        settings_cache,
        settings,
    ):
        settings_cache = json.loads(settings_cache)

        # Create settings dict by looking at the callback inputs
        if isinstance(ctx.args_grouping, dict):
            settings = {
                i["id"].removeprefix("einstellung_"): i["value"]
                for i in ctx.args_grouping["settings"].values()
            }

        # Wenn auf "Zurücksetzen" gedrückt wird, gehe durch jede Änderung durch und setze jede Einstellung auf ihren vorigen Wert bzw. den Standardwert zurück
        if ctx.triggered_id == "settings_btn_reset":
            for key in settings.keys():
                set_props(
                    "einstellung_" + key,
                    {"value": settings_cache.get(key, DEFAULT_SETTINGS[key])},
                )
            return no_update, no_update, no_update

        # Aktualisiere das Cache mit den vorgenommenen Einstellungen
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

    # Setze ein Feld ein zur manuellen Eingabe von Zeiten, wie oft ein Backup durchgeführt werden soll, wenn die entsprechende Option ausgewählt wird
    @app.callback(
        Output("settings_wrapper_input_backup_frequency", "display"),
        Input("settings_select_backup_frequency", "value"),
        State("settings_input_backup_frequency", "value"),
    )
    def add_input(value_häufigkeit, value_minuten):
        # Wenn der Wert auf "interval" gesetzt wird, mache das Eingabefeld für die Minuten sichtbar
        if value_häufigkeit == "interval":
            return "flex"
        # Bei jedem anderen Wert wird das hinzugefügte Feld wieder ausgeblendet
        elif value_minuten:
            return "None"

    # Regelt die Logik für die Backups.
    @app.callback(
        Output("notifications", "sendNotifications", allow_duplicate=True),
        Input("cache_settings", "data"),
        Input("interval_backup_frequency", "n_intervals"),
        prevent_initial_call=False,
    )
    def make_backup(einstellungen_cache, n_intervals):
        if einstellungen_cache != None:
            cache = json.loads(einstellungen_cache)
        else:
            raise PreventUpdate

        messages = [
            dict(
                title="Backup erstellt!",
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

        if (
            cache.get("settings_select_backup_frequency") == "open"
        ):  # Wegen prevent_initial_call = False wird das Callback bei jedem Neuladen oder Aufrufen der Seite durchgeführt, wodurch mit copy_and_rename ein Backup erstellt wird
            functions.backup_db()
            return messages
        elif (
            cache.get("settings_select_backup_frequency") == "interval"
            and ctx.triggered_id == "interval_backup_frequency"
        ):
            functions.backup_db()
            return messages

    # Startet oder stoppt den Timer für die intervallbasierten Backups
    @app.callback(
        Output("interval_backup_frequency", "disabled"),
        Output("interval_backup_frequency", "interval"),
        Input("cache_settings", "data"),
        prevent_initial_call=False,
    )
    def make_interval_backup(einstellungen_cache):
        if einstellungen_cache != None:
            cache = json.loads(einstellungen_cache)
        else:
            raise PreventUpdate

        frequency_ms = cache.get("settings_input_backup_frequency") * 60 * 1000
        if cache.get("settings_select_backup_frequency") == "interval":
            return False, frequency_ms
        else:
            return True, no_update

    # Controls the buttons in the settings for importing, exporting and creating a database
    @app.callback(
        Output("settings_download_export_database", "data"),
        Output("modal_confirm_backup", "opened"),
        Output("cache_current_database", "data"),
        Output("settings_btn_import_database", "contents"),
        Input("settings_btn_export_database", "n_clicks"),
        Input("settings_btn_create_database", "n_clicks"),
        Input("settings_btn_import_database", "contents"),
    )
    def database_tools(export_n_clicks, neu_n_clicks, import_data):
        db = Path(f"current.sqlite")

        if ctx.triggered_id == "settings_btn_export_database":
            # Returns the currently opened database to the download component
            return (
                dcc.send_file(db),
                no_update,
                no_update,
                no_update,
            )

        if ctx.triggered_id == "settings_btn_import_database":
            # Cut of the type description when importing the table.
            type, content = import_data.split(",")

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
            db.write_bytes(
                base64.b64decode(content)
            )  # Schreibe den hochgeladenen Inhalt in die Datei

            # The last "None" is important for resetting the upload component
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

    # Controls the buttons of the modal, which backups the database when importing an existing or creating a new one
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
        ja_n_clicks, nein_n_clicks, abbrechen_n_clicks, import_data
    ):
        import_data = json.loads(import_data)
        mode = import_data.get("mode")

        content_encoded = import_data.get("content")
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

    # Öffnet das Modal zu den Füllmengen
    @app.callback(
        Output("modal_linechart_amount", "opened"),
        Output("chart_amount", "data"),
        Input("wrapper_sparkline_amount", "n_clicks"),
        State("modal_linechart_amount", "opened"),
        State("main_table", "selectedRows"),
    )
    def open_füllstände_verlauf(n_clicks, opened, rows):
        barcode = rows[0].get("barcode", "")
        data = functions.get_füllmenge_data(barcode)
        return True, data

    # Führe Keyboard-Shortcuts aus
    @app.callback(
        Input("eventlistener_keyboard", "n_events"),
        Input("eventlistener_keyboard", "event"),
        State("wrapper_entry", "hidden"),
        State("modal_new_entry", "opened"),
        State("btn_save_entry", "n_clicks"),
        State("modal_btn_save_entry", "n_clicks"),
        State("modal_btn_save_entry", "disabled"),
        State("btn_create_new_entry", "n_clicks"),
        State("modal_confirm_save", "opened"),
        State("save_btn_yes", "n_clicks"),
        State("btn_create_new_entry", "disabled"),
    )
    def execute_shortcut(
        n_events,
        event,
        is_input_hidden,
        is_neuer_eintrag_open,
        eintrag_speichern_n_clicks,
        neuen_eintrag_speichern_n_clicks,
        is_modal_speichern_disabled,
        neuer_eintrag_n_clicks,
        is_speichern_bestätigung_open,
        speichern_bestätigung_ja_n_clicks,
        is_neuer_eintrag_disabled,
    ):
        key = event.get("key")
        is_shift = event.get("shiftKey")
        is_metaKey = event.get("metaKey")
        is_ctrlKey = event.get("ctrlKey")
        tag_name = event.get("target.tagName")
        if is_shift:
            if key == "Enter":
                if not is_input_hidden and not is_neuer_eintrag_open:
                    set_props("modal_confirm_save", {"opened": True})
                    return
                elif is_neuer_eintrag_open and not is_modal_speichern_disabled:
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
                        and not is_neuer_eintrag_open
                        and not is_neuer_eintrag_disabled
                    ):
                        set_props(
                            "btn_create_new_entry",
                            {"n_clicks": neuer_eintrag_n_clicks + 1},
                        )
                        return

    # Kontrolliert die Logik hinter dem "Eintrag Speichern" Modal
    @app.callback(
        Output("modal_confirm_save", "opened"),
        Input("save_btn_yes", "n_clicks"),
        Input("save_btn_cancel", "n_clicks"),
        State("btn_save_entry", "n_clicks"),
        State("modal_btn_save_entry", "n_clicks"),
        State("modal_new_entry", "opened"),
    )
    def confirm_save(
        ja_n_clicks,
        abbrechen_n_clicks,
        eintrag_speichern_n_clicks,
        neuen_eintrag_speichern_n_clicks,
        is_neuer_eintrag_open,
    ):

        if ctx.triggered_id == "save_btn_yes":
            if is_neuer_eintrag_open:
                set_props(
                    "modal_btn_save_entry",
                    {"n_clicks": neuen_eintrag_speichern_n_clicks + 1},
                )
            elif not is_neuer_eintrag_open:
                set_props(
                    "btn_save_entry", {"n_clicks": eintrag_speichern_n_clicks + 1}
                )
        elif ctx.triggered_id == "save_btn_cancel":
            pass

        return False

    # Control the logic of the archive button
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
    def open_archive(n_clicks, leftSection):
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

        if not leftSection:
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

    # Control the logic of the to_archive Button
    @app.callback(
        Output("main_table", "rowData", allow_duplicate=True),
        Output("notifications", "sendNotifications", allow_duplicate=True),
        Input("btn_archive_entry", "n_clicks"),
        State("input_name", "leftSection"),
        State("main_table", "selectedRows"),
    )
    def transfer_to_archive(n_clicks, left_section, rows):
        barcode = rows[0].get("barcode", "")

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
    def toggle_gestis_button(value: str):
        if value == "":
            return True, ""
        else:
            value = value.rjust(6, "0")
            return False, f"https://gestis.dguv.de/data?name={value}"
