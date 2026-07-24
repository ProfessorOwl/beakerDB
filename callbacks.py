from dash_iconify import DashIconify
from dash import (
    Input,
    Output,
    State,
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
import datetime as dt
import icons
from pathlib import Path
import shutil

DEFAULT_SETTINGS = json.loads(Path("default_settings.json").read_bytes())
TODAY = dt.date.today().isoformat()


def get_callbacks(app):

    # Initialize the main table with fresh data from the database.
    # The input of mainWrapper is just a dummy. The callback gets fired everytime mainWrapper is initialized on the website by default.
    @app.callback(
        Output("mainGrid", "rowData"),
        Input("mainWrapper", "children"),
        prevent_initial_call=False,
    )
    def init_mainGrid(children):
        return functions.getMainTable().to_dict("records")

    # Callback das jedes Feld aktualisiert, sobald man eine neue Zeile in der Tabelle auswählt
    @app.callback(
        Output("input-barcode", "value"),
        Output("input-name", "value"),
        Output("input-summenformel", "value"),
        Output("input-cas-nr", "value"),
        Output("input-mengeneinheit", "value"),
        Output("input-füllmenge", "value"),
        Output("input-kaufdatum", "value"),
        Output("input-lieferant", "value"),
        Output("input-hersteller", "value"),
        Output("input-raum", "value"),
        Output("input-reinheit", "value"),
        Output("input-konzentration", "value"),
        Output("input-molmasse", "value"),
        Output("input-lösungsmittel", "value"),
        Output("input-geprüft", "value"),
        Output("button-speichern", "disabled"),
        Output("button-löschen", "disabled"),
        Output("inputContainer", "hidden"),
        Output("inputPlaceholder", "display"),
        Input("mainGrid", "selectedRows"),
    )
    def update_fields(rows):
        if not rows:  # Wenn nichts ausgewählt ist
            return (
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
                "",
                True,  # Blende den Speicher-Button aus
                True,  # Blende den Löschen-Button aus
                True,  # Blende "inputContainer" aus
                "flex",  # Blende den Platzhalter ein
            )
        barcode = rows[0].get("Barcode", "")
        return (
            barcode,
            *[  # Gebe für jedes Feld den entsprechenden Wert aus der Inventartabelle zurück
                functions.selectInInventory(barcode, x)
                for x in [
                    "name",
                    "summenformel",
                    "cas_nr",
                    "mengeneinheit_id",
                    "füllmenge",
                    "kaufdatum",
                    "lieferant_id",
                    "hersteller_id",
                    "raum_id",
                    "reinheit",
                    "konzentration",
                    "molmasse",
                    "lösungsmittel",
                    "zuletzt_geprüft",
                ]
            ],
            False,
            False,
            False,
            "None",
        )

    # Sobald der Speicherbutton gedrückt wird, aktualisiere die Werte in der sichtbaren Tabelle wie auch in der Datenbank
    @app.callback(
        Output("mainGrid", "rowData", allow_duplicate=True),
        Output("notification-container", "sendNotifications"),
        Input("button-speichern", "n_clicks"),
        State("input-name", "value"),
        State("input-barcode", "value"),
        State("input-füllmenge", "value"),
        State("input-kaufdatum", "value"),
        State("input-hersteller", "value"),
        State("input-lieferant", "value"),
        State("input-raum", "value"),
        State("input-reinheit", "value"),
        State("input-konzentration", "value"),
        State("input-lösungsmittel", "value"),
        State("input-cas-nr", "value"),
        State("input-molmasse", "value"),
        State("input-summenformel", "value"),
        State("input-mengeneinheit", "value"),
        State("input-geprüft", "value"),
        State("einstellungenCache", "data"),
    )
    def save_data(
        n_clicks,
        name,
        barcode,
        füllmenge,
        kaufdatum,
        herstellerID,
        lieferantID,
        raumID,
        reinheit,
        konzentration,
        lösungsmittel,
        casnr,
        molmasse,
        summenformel,
        mengeneinheitID,
        zuletzt_geprüft,
        einstellungen_cache,
    ):
        # Falls die Felder leer sind trage 0 ein, was dem leeren Wert in der SQL-Tabelle entspricht
        if herstellerID == None or "":
            herstellerID = 0
        if lieferantID == None or "":
            lieferantID = 0
        if raumID == None or "":
            raumID = 0
        if mengeneinheitID == None or "":
            mengeneinheitID = 0

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

        if "," in str(füllmenge):
            füllmenge = füllmenge.replace(",", ".")
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
        if "," in str(molmasse):
            molmasse = molmasse.replace(",", ".")
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
        # Überprüfe, ob die Einstellung aktiviert ist, bei der das Datum beim Speichern automatisch auf das heutige gesetzt wird.
        # Wenn ja, dann gebe hänge eine Nachricht an, dass das geschehen ist und überschreibe das vorherige Datum mit heute.
        einstellungen_cache = json.loads(einstellungen_cache)
        if (
            einstellungen_cache.get("datumsänderung") == "change"
            or einstellungen_cache.get("datumsänderung") == "createchange"
        ) and zuletzt_geprüft != TODAY:
            zuletzt_geprüft = TODAY
            set_props("input-geprüft", {"value": zuletzt_geprüft})
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

        # Trage alle Werte in der Datenbank ein
        functions.updateInInventory(
            barcode,
            [
                "name",
                "barcode",
                "füllmenge",
                "kaufdatum",
                "reinheit",
                "konzentration",
                "lösungsmittel",
                "cas_nr",
                "molmasse",
                "summenformel",
                "hersteller_id",
                "lieferant_id",
                "raum_id",
                "mengeneinheit_id",
                "zuletzt_geprüft",
            ],
            [
                name,
                barcode,
                füllmenge,
                kaufdatum,
                reinheit,
                konzentration,
                lösungsmittel,
                casnr,
                molmasse,
                summenformel,
                herstellerID,
                lieferantID,
                raumID,
                mengeneinheitID,
                zuletzt_geprüft,
            ],
        )

        df = functions.getMainTable()

        return (
            df.to_dict("records"),
            messages,
        )

    # Sobald der "Löschen"-Button gedrückt wird, soll die Zeile sowohl aus der sichtbaren Tabelle, wie auch der SQL-Datenbank gelöscht werden
    @app.callback(
        Output("mainGrid", "rowData", allow_duplicate=True),
        Output("notification-container", "sendNotifications", allow_duplicate=True),
        Output("mainGrid", "selectedRows", allow_duplicate=True),
        Input("button-löschen", "n_clicks"),
        State("mainGrid", "selectedRows"),
    )
    def removeRow(n_clicks, rows):
        barcode = rows[0].get("Barcode", "")
        functions.deleteInInventory(barcode)
        global df  # Greife auf den globalen Dataframe zurück, damit die Tabelle auch nach Pagerefresh oder auf einem anderen Computer geändert ist
        df = functions.getMainTable()
        return (
            df.to_dict("records"),
            [
                dict(  # ...und gebe eine Notifikation heraus
                    title="Eintrag gelöscht!",
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
        )

    # Öffne bzw. schließe das Fenster, in dem ein neuer Eintrag hinzugefügt werden kann und setze alle Felder zurück
    @app.callback(
        Output("modalNeuerEintrag", "opened"),
        Output(
            "modal-button-speichern",
            "disabled",
            allow_duplicate=True,
        ),
        Output("modal-input-barcode", "error", allow_duplicate=True),
        Output("modal-input-name", "value"),
        Output("modal-input-barcode", "value"),
        Output("modal-input-summenformel", "value"),
        Output("modal-input-cas-nr", "value"),
        Output("modal-input-mengeneinheit", "value"),
        Output("modal-input-füllmenge", "value"),
        Output("modal-input-kaufdatum", "value"),
        Output("modal-input-lieferant", "value"),
        Output("modal-input-hersteller", "value"),
        Output("modal-input-raum", "value"),
        Output("modal-input-reinheit", "value"),
        Output("modal-input-konzentration", "value"),
        Output("modal-input-molmasse", "value"),
        Output("modal-input-lösungsmittel", "value"),
        Output("modal-input-geprüft", "value"),
        Input("button-open-modal", "n_clicks"),
        Input("modal-button-abbrechen", "n_clicks"),
        Input("modal-button-speichern", "n_clicks"),
        State("einstellungenCache", "data"),
        State("modalNeuerEintrag", "opened"),
    )
    def openModalNeuerEintrag(
        n_clicks1, n_clicks2, n_clicks3, einstellungen_cache, opened
    ):
        einstellungen_cache = json.loads(einstellungen_cache)
        if (
            einstellungen_cache.get("datumsänderung") == "create"
            or einstellungen_cache.get("datumsänderung") == "createchange"
        ):
            input_geprüft = TODAY
        else:
            input_geprüft = ""

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
        )

    # Gebe einen Fehler zurück, wenn der Barcode bereits vergeben ist
    @app.callback(
        Output("modal-input-barcode", "error", allow_duplicate=True),
        Output(
            "modal-button-speichern",
            "disabled",
            allow_duplicate=True,
        ),
        Input("modal-input-barcode", "n_blur"),
        State("modal-input-barcode", "value"),
    )
    def is_barcode_used(n_blur, barcode):
        selected = functions.selectInInventory(barcode, "barcode")
        if "" == barcode:
            return ("Barcode darf nicht leer sein", True)
        elif selected == barcode:
            return ("Barcode ist bereits vergeben", True)
        else:
            return (None, False)

    # Speichere den neuen Eintrag
    @app.callback(
        Output("mainGrid", "rowData", allow_duplicate=True),
        Output("notification-container", "sendNotifications", allow_duplicate=True),
        Input("modal-button-speichern", "n_clicks"),
        State("modal-input-name", "value"),
        State("modal-input-barcode", "value"),
        State("modal-input-füllmenge", "value"),
        State("modal-input-kaufdatum", "value"),
        State("modal-input-hersteller", "value"),
        State("modal-input-lieferant", "value"),
        State("modal-input-raum", "value"),
        State("modal-input-reinheit", "value"),
        State("modal-input-konzentration", "value"),
        State("modal-input-lösungsmittel", "value"),
        State("modal-input-cas-nr", "value"),
        State("modal-input-molmasse", "value"),
        State("modal-input-summenformel", "value"),
        State("modal-input-mengeneinheit", "value"),
        State("modal-input-geprüft", "value"),
    )
    def save_new_data(
        n_clicks,
        name,
        barcode,
        füllmenge,
        kaufdatum,
        herstellerID,
        lieferantID,
        raumID,
        reinheit,
        konzentration,
        lösungsmittel,
        casnr,
        molmasse,
        summenformel,
        mengeneinheitID,
        zuletzt_geprüft,
    ):
        # Falls die ID-Felder leer sind trage 0 ein, was dem "Nicht ausgewählt" in der SQL-Tabelle entspricht
        if herstellerID == None or "":
            herstellerID = 0
        if lieferantID == None or "":
            lieferantID = 0
        if raumID == None or "":
            raumID = 0
        if mengeneinheitID == None or "":
            mengeneinheitID = 0
        # Trage bei den Reelen Zahlen None ein, falls sie leer gelassen werden. "" gibt als String andernfalls einen Fehler.
        if füllmenge == "":
            füllmenge = None
        if molmasse == "":
            molmasse = None

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

        if "," in str(füllmenge) and füllmenge:
            füllmenge = füllmenge.replace(",", ".")
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

        if "," in str(molmasse) and molmasse:
            molmasse = molmasse.replace(",", ".")
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

        # Trage alle Werte in der Datenbank ein
        functions.createInInventory(
            [
                "name",
                "barcode",
                "füllmenge",
                "kaufdatum",
                "reinheit",
                "konzentration",
                "lösungsmittel",
                "cas_nr",
                "molmasse",
                "summenformel",
                "hersteller_id",
                "lieferant_id",
                "raum_id",
                "mengeneinheit_id",
                "zuletzt_geprüft",
            ],
            [
                name,
                barcode,
                füllmenge,
                kaufdatum,
                reinheit,
                konzentration,
                lösungsmittel,
                casnr,
                molmasse,
                summenformel,
                herstellerID,
                lieferantID,
                raumID,
                mengeneinheitID,
                zuletzt_geprüft,
            ],
        )

        global df  # Greife auf den globalen Dataframe zurück, damit die Tabelle auch nach Pagerefresh oder auf einem anderen Computer geändert ist
        df = functions.getMainTable()
        return (
            df.to_dict("records"),
            messages,
        )

    # Öffne und schließe das Modal, in dem die Stammdaten bearbeitet werden können und initialisiere die Stammdatentabelle mit dem letzten Wert des Selectors. Setze die Stammdatentabelle zurück, wenn auf "Änderungen zurücksetzen" geclickt wird.
    @app.callback(
        Output("modalStammdaten", "opened"),
        Output("stammGrid", "columnDefs"),
        Output("stammGrid", "rowData"),
        Output("stammdatenCache", "data", allow_duplicate=True),
        Output("notification-container", "clean"),
        Output("stammdatenButtonZurücksetzen", "disabled"),
        Output("stammdatenButtonSpeichern", "disabled"),
        Input("button-stammdaten", "n_clicks"),
        Input("stammdatenButtonZurücksetzen", "n_clicks"),
        Input("stammdatenButtonAbbrechen", "n_clicks"),
        Input("selectStammdaten", "value"),
        State("modalStammdaten", "opened"),
    )
    def openModalStammdaten(
        n_clicksModal, n_clicksZurücksetzen, n_clicksAbbrechen, selector, opened
    ):
        if ctx.triggered_id == "stammdatenButtonAbbrechen":
            return not opened, no_update, no_update, no_update, no_update, True
        df = pd.read_sql(
            f"SELECT * from {selector}",
            "sqlite:///current.sqlite",
            dtype_backend="pyarrow",
        )
        headings = functions.getHeadings(selector)
        cache = dict()
        columnDefs = [
            {"field": i, "sortable": True, "editable": True} for i in headings
        ]
        columnDefs[-1].update(
            {"flex": True}
        )  # Letzte Spalte füllt den übrigen Raum aus
        columnDefs[0].update(
            {"editable": False}
        )  # Erste Spalte (Primärschlüssel) ist nicht editierbar

        if ctx.triggered_id == "stammdatenButtonZurücksetzen":
            return (
                no_update,
                columnDefs,
                df.to_dict("records"),
                json.dumps(
                    cache
                ),  # dcc.Store kann nur JSON Dateien empfangen, also muss das Cache immer als JSON exportiert/importiert werden
                True,
                True,
                True,
            )

        if ctx.triggered_id == "selectStammdaten":
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

    # Delete all notifications in the in the queue and currently displayed when the modal is opened or closed
    @app.callback(
        Output("notification-container", "clean", allow_duplicate=True),
        Input("modalStammdaten", "opened"),
    )
    def cleanNotificationContainer(opened):
        return True

    # Füge mit den Buttons Zeilen zur Stammdatentabelle hinzu oder lösche sie
    @app.callback(
        Output("stammGrid", "rowTransaction"),
        Output("stammGrid", "deleteSelectedRows"),
        Output("stammdatenCache", "data", allow_duplicate=True),
        Output("stammdatenButtonZurücksetzen", "disabled", allow_duplicate=True),
        Output("stammdatenButtonSpeichern", "disabled", allow_duplicate=True),
        Input("stammdatenButtonZeileHinzufügen", "n_clicks"),
        Input("stammdatenButtonZeileLöschen", "n_clicks"),
        State("stammGrid", "rowData"),
        State("stammGrid", "columnDefs"),
        State("stammdatenCache", "data"),
        State("stammGrid", "selectedRows"),
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
        for i in range(len(firstColumnEntries) - 1):
            diff = firstColumnEntries[i + 1] - firstColumnEntries[i]
            if diff > 1:
                unusedID = firstColumnEntries[i] + 1

        if unusedID == None:
            unusedID = firstColumnEntries[-1] + 1

        # Wenn auf "Zeile hinzufügen" gedrückt wird:
        if ctx.triggered_id == "stammdatenButtonZeileHinzufügen":
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
        if ctx.triggered_id == "stammdatenButtonZeileLöschen":
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

    # Speichere die Zeilen im Cache ab, wenn ein Zeileneintrag geändert wird
    @app.callback(
        Output("stammdatenCache", "data", allow_duplicate=True),
        Output("stammdatenButtonZurücksetzen", "disabled", allow_duplicate=True),
        Output("stammdatenButtonSpeichern", "disabled", allow_duplicate=True),
        Input("stammGrid", "cellValueChanged"),
        State("stammdatenCache", "data"),
        State("stammGrid", "columnDefs"),
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
        Output("stammdatenCache", "data", allow_duplicate=True),
        Output("notification-container", "sendNotifications", allow_duplicate=True),
        Output("stammdatenButtonZurücksetzen", "disabled", allow_duplicate=True),
        Output("stammdatenButtonSpeichern", "disabled", allow_duplicate=True),
        Input("stammdatenButtonSpeichern", "n_clicks"),
        State("selectStammdaten", "value"),
        State("stammdatenCache", "data"),
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
                    columns.append(c)
                    values.append(v)
                if c == "op":
                    op = v
            # Falls ein Fehler passiert, hänge eine Nachricht an
            if len(columns) == 0:
                messages.append(
                    dict(  # ...und gebe eine Notifikation heraus
                        title="Zeilen dürfen keine leeren Einträge besitzen!",
                        message=f"Die Zeile mit ID {id} wurde nicht gespeichert. Ändere den Inhalt der Zeile, sonst wird sie verworfen.",
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
                            title=f"Fehler beim Aktualisieren des Eintrages mit ID {id}",
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
                            title=f"Fehler beim Löschen des Eintrages mit ID {id}",
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
                            title=f"Fehler beim Einfügen des Eintrages mit ID {id}",
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
                        title="Fehler",
                        message=f'Die Operation "{op}" konnte für ID {id} nicht gefunden werden.',
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
        # else:
        #     return json.dumps(modify_cache), messages, is_disabled, is_disabled

    # Aktualisiere alle Select-Felder, die Daten aus der Datenbank anzeigen, nachdem die Datenbank modifiziert wurde. Dadurch werden keine veralteten Daten angezeigt.
    @app.callback(
        Output("input-selectFromDatabase", "data"),
        Output("input-mengeneinheit", "data"),
        Output("input-hersteller", "data"),
        Output("input-lieferant", "data"),
        Output("input-raum", "data"),
        Output("modal-input-selectFromDatabase", "data"),
        Output("modal-input-mengeneinheit", "data"),
        Output("modal-input-hersteller", "data"),
        Output("modal-input-lieferant", "data"),
        Output("modal-input-raum", "data"),
        Input("stammdatenButtonSpeichern", "n_clicks"),
    )
    def updateLists(n_clicks):
        return (
            functions.generateSelectData_Namen(),
            functions.generateSelectData(
                functions.Mengeneinheiten,
                ["mengeneinheit_id", "mengeneinheit"],
            ),
            functions.generateSelectData(
                functions.Hersteller, ["hersteller_id", "hersteller"]
            ),
            functions.generateSelectData(
                functions.Lieferanten, ["lieferant_id", "lieferant"]
            ),
            functions.generateSelectData_Räume(),
            functions.generateSelectData_Namen(),
            functions.generateSelectData(
                functions.Mengeneinheiten,
                ["mengeneinheit_id", "mengeneinheit"],
            ),
            functions.generateSelectData(
                functions.Hersteller, ["hersteller_id", "hersteller"]
            ),
            functions.generateSelectData(
                functions.Lieferanten, ["lieferant_id", "lieferant"]
            ),
            functions.generateSelectData_Räume(),
        )

    # Initialisiere den Scan-Script, der zwischen normalem Input und gescannten Input unterscheidet. Scanner soll als normale Tastatur funktionieren, wenn Stammdaten- oder "Neuer Eintrag"-Fenster geöffnet ist.
    clientside_callback(
        ClientsideFunction(namespace="helper", function_name="initScanner"),
        Output("scanListener", "id"),
        Input("scanListener", "id"),
        Input("modalNeuerEintrag", "opened"),
        Input("modalStammdaten", "opened"),
        prevent_initial_call=False,
    )

    # Search for the string that the scanListener returns after firing and select the first available entry
    @app.callback(
        Output("mainGrid", "filterModel"),
        Output("mainGrid", "selectedRows"),
        Input("scanListener", "n_events"),
        State("scanListener", "event"),
        State("modalNeuerEintrag", "opened"),
        State("modalStammdaten", "opened"),
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
            "Barcode": {
                "filterType": "text",
                "type": "contains",
                "filter": barcode,
            }
        }
        return filter, [{"Barcode": barcode}]

    # Reset all filters from mainGrid when the Filter button is pressed
    @app.callback(
        Output("mainGrid", "filterModel", allow_duplicate=True),
        Output("button-filter-reset", "disabled"),
        Input("button-filter-reset", "n_clicks"),
        Input("mainGrid", "filterModel"),
    )
    def resetFilter(n_clicks, filterModel):
        if ctx.triggered_id == "button-filter-reset":
            return {}, True
        elif ctx.triggered_id == "mainGrid":
            if len(filterModel) == 0:
                return no_update, True
            else:
                return no_update, False

    # Fill a new or existing entry with the contents of the gestis database or another existing entry
    @app.callback(
        Output("modal-input-popover", "opened"),
        Output("input-popover", "opened"),
        Input("input-selectFromDatabaseConfirm", "n_clicks"),
        Input("modal-input-selectFromDatabaseConfirm", "n_clicks"),
        State("input-selectFromDatabase", "value"),
        State("modal-input-selectFromDatabase", "value"),
    )
    def updateFromExistingData(n_clicks, n_clicksModal, value, valueModal):
        modalPrefix = ""
        if ctx.triggered_id == "modal-input-selectFromDatabaseConfirm":
            modalPrefix = "modal-"
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
                set_props(modalPrefix + field, {"value": i})

        setField("cas_nr", "input-cas-nr")
        setField("name", "input-name")
        setField("summenformel", "input-summenformel")
        setField("raum_id", "input-raum")
        setField("lieferant_id", "input-lieferant")
        setField("mengeneinheit_id", "input-mengeneinheit")
        setField("kaufdatum", "input-kaufdatum")
        setField("hersteller_id", "input-hersteller")
        setField("reinheit", "input-reinheit")
        setField("konzentration", "input-konzentration")
        setField("lösungsmittel", "input-lösungsmittel")
        setField("molmasse", "input-molmasse")

        if (
            ctx.triggered_id == "modal-input-selectFromDatabaseConfirm"
        ):  # Schließe das Modal, wenn auf "Eintrag übernehmen" gedrückt wird
            return False, no_update
        else:
            return no_update, False

    # Set the input of the database search selector to a blank string when it gets opened
    @app.callback(
        Input("input-popover", "opened"),
        Input("modal-input-popover", "opened"),
    )
    def resetSelectFromDatabase(opened, modalOpened):
        if ctx.triggered_id == "input-popover":
            set_props("input-selectFromDatabase", {"value": None})
        elif ctx.triggered_id == "modal-input-popover":
            set_props("modal-input-selectFromDatabase", {"value": None})

    # Setze das Datum auf Heute bei den DateInput-Selektoren, wenn auf den "Heute"-Button gedrückt wird
    @app.callback(
        Input("input-kaufdatum-heute", "n_clicks"),
        Input("modal-input-kaufdatum-heute", "n_clicks"),
        Input("input-geprüft-heute", "n_clicks"),
        Input("modal-input-geprüft-heute", "n_clicks"),
    )
    def setDateToToday(
        n_clicks_kaufdatumHeute,
        n_clicks_modalKaufdatumHeute,
        n_clicks_geprüftHeute,
        n_clicks_modalGeprüftHeute,
    ):
        input_ids = [
            "input-kaufdatum-heute",
            "modal-input-kaufdatum-heute",
            "input-geprüft-heute",
            "modal-input-geprüft-heute",
        ]
        # Setzt den Output des Feldes auf das heutige Datum, wenn der Button vom Feld gedrückt wird.
        # Entferne dafür "-heute" hinter der ID, um auf das Feld und nicht den Button zu verweisen.
        for id in input_ids:
            if ctx.triggered_id == id:
                set_props(id.removesuffix("-heute"), {"value": TODAY})
        return

    # Öffne oder schließe das Einstellungsmenü
    @app.callback(
        Output("modalEinstellungen", "opened"),
        Input("button-einstellungen", "n_clicks"),
        Input("einstellungenButtonAbbrechen", "n_clicks"),
        State("modalEinstellungen", "opened"),
        State("einstellungenCache", "data"),
    )
    def toggleSettings(n_clicks_Öffnen, n_clicks_Abbrechen, opened, cache):
        if ctx.triggered_id == "einstellungenButtonAbbrechen":
            return not opened

        cache = json.loads(cache)

        for (
            key,
            value,
        ) in (
            cache.items()
        ):  # Falls die Einstellung im Cache ist, setze ihren Wert auf den gespeicherten Wert im Cache
            set_props("einstellung_" + key, {"value": value})
        return not opened

    # Initialisiere das Cache mit den Einstellungen
    @app.callback(
        Output("einstellungenCache", "data", allow_duplicate=True),
        State("einstellungenCache", "data"),
        prevent_initial_call=False,
    )
    def init_settings(einstellungen_cache):
        if einstellungen_cache == None:
            return json.dumps(DEFAULT_SETTINGS)
        else:
            return no_update

    # Speichere die Daten der Einstellungen im Browser ab
    @app.callback(
        Output("einstellungenCache", "data", allow_duplicate=True),
        Output("modalEinstellungen", "opened", allow_duplicate=True),
        Output("notification-container", "sendNotifications", allow_duplicate=True),
        Input("einstellungenButtonSpeichern", "n_clicks"),
        Input("einstellungenButtonZurücksetzen", "n_clicks"),
        State("einstellungenCache", "data"),
        State("einstellung_datumsänderung", "value"),
        State("einstellung_backup_häufigkeit", "value"),
        State("einstellung_backup_häufigkeit_minuten", "value"),
    )
    def saveSettings(
        n_clicks_speichern,
        n_clicks_zurücksetzen,
        cache,
        datumsänderung,
        backup_häufigkeit,
        backup_häufigkeit_minuten,
    ):
        cache = json.loads(cache)

        settings = {  # Jede Einstellung muss hier explizit aufgeführt werden
            "datumsänderung": datumsänderung,
            "backup_häufigkeit": backup_häufigkeit,
            "backup_häufigkeit_minuten": backup_häufigkeit_minuten,
        }

        # Wenn auf "Zurücksetzen" gedrückt wird, gehe durch jede Änderung durch und setze jede Einstellung auf ihren vorigen Wert bzw. den Standardwert zurück
        if ctx.triggered_id == "einstellungenButtonZurücksetzen":
            for key in settings.keys():
                set_props(
                    "einstellung_" + key,
                    {"value": cache.get(key, DEFAULT_SETTINGS[key])},
                )
            raise PreventUpdate

        # Aktualisiere das Cache mit den vorgenommenen Einstellungen
        cache.update(settings)

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

        return json.dumps(cache), False, messages

    # Setze ein Feld ein zur manuellen Eingabe von Zeiten, wie oft ein Backup durchgeführt werden soll, wenn die entsprechende Option ausgewählt wird
    @app.callback(
        Output("einstellung_backup_häufigkeit_minuten_container", "display"),
        Input("einstellung_backup_häufigkeit", "value"),
        State("einstellung_backup_häufigkeit_minuten", "value"),
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
        Output("notification-container", "sendNotifications", allow_duplicate=True),
        Input("einstellungenCache", "data"),
        Input("einstellung_backup_häufigkeit_helper", "n_intervals"),
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
            cache.get("backup_häufigkeit") == "open"
        ):  # Wegen prevent_initial_call = False wird das Callback bei jedem Neuladen oder Aufrufen der Seite durchgeführt, wodurch mit copy_and_rename ein Backup erstellt wird
            functions.backup_db()
            return messages
        elif (
            cache.get("backup_häufigkeit") == "interval"
            and ctx.triggered_id == "einstellung_backup_häufigkeit_helper"
        ):
            functions.backup_db()
            return messages

    # Startet oder stoppt den Timer für die intervallbasierten Backups
    @app.callback(
        Output("einstellung_backup_häufigkeit_helper", "disabled"),
        Output("einstellung_backup_häufigkeit_helper", "interval"),
        Input("einstellungenCache", "data"),
        prevent_initial_call=False,
    )
    def make_interval_backup(einstellungen_cache):
        if einstellungen_cache != None:
            cache = json.loads(einstellungen_cache)
        else:
            raise PreventUpdate

        häufigkeit_ms = cache.get("backup_häufigkeit_minuten") * 60 * 1000
        if cache.get("backup_häufigkeit") == "interval":
            return False, häufigkeit_ms
        else:
            return True, no_update

    # Kontrolliert die Buttons im Einstellungsmenü für das Importieren, Exportieren und erstellen einer Datenbank
    @app.callback(
        Output("einstellung_datenbank_exportieren_download", "data"),
        Output("modalBestätigungImport", "opened"),
        Output("current_db_cache", "data"),
        Output("einstellung_datenbank_importieren_daten", "contents"),
        Input("einstellung_datenbank_exportieren", "n_clicks"),
        Input("einstellung_datenbank_neu", "n_clicks"),
        Input("einstellung_datenbank_importieren_daten", "contents"),
    )
    def database_tools(export_n_clicks, neu_n_clicks, import_data):
        dest_path = Path(f"current.sqlite")
        if ctx.triggered_id == "einstellung_datenbank_exportieren":
            src_path = Path("current.sqlite")

            return (
                dcc.send_file(src_path),
                no_update,
            )  # Gibt die momentan geöffnete Datenbank an die Download-Komponente weiter

        if ctx.triggered_id == "einstellung_datenbank_importieren_daten":
            type, content = import_data.split(",")
            content_decoded = base64.b64decode(
                content
            )  # Der von der Upload-Komponente bereitgestellte Inhalt ist immer Base64-verschlüsselt, daher muss er erst entschlküsselt werden.

            try:  # Falls keine Datenbank vorhanden ist, so wird eine leere current.sqlite-Datei erstellt.
                Path.touch(dest_path, exist_ok=False)
            except:  # Ansonsten wird ein Modal geöffnet, um die geöffnete Datenbank noch zu archivieren oder zu überschreiben.
                return no_update, True, json.dumps(content), None

            dest_path.write_bytes(
                content_decoded
            )  # Schreibe den hochgeladenen Inhalt in die Datei

            return (
                no_update,
                no_update,
                no_update,
                None,
            )  # Das letzte "None" ist wichtig, da ansonsten die Upload-Komponente nicht mehr richtig funktioniert.

        if ctx.triggered_id == "einstellung_datenbank_neu":
            src_path = Path("blank.sqlite")  # Der Pfad zu einer leeren Datenbank
            blank = src_path.open(mode="rb")  # Öffne sie im Binärmodus

            if Path.exists(
                dest_path
            ):  # Falls bereits eine Datenbank existiert, so öffne auch hier den Dialog, um zu bestimmen, was mit der geöffneten Datenbank passieren soll.
                return (
                    no_update,
                    True,
                    json.dumps(
                        base64.b64encode(blank.read()).decode()
                    ),  # Das Cache kann nur JSON-Dateien entgegennehmen. Daher muss der Dateiinhalt in Base64 verschlüsselt werde und in einen String dekodiert werden.
                    None,
                )
            else:
                shutil.copy(src_path, dest_path)
            return no_update, no_update, no_update, None

    # Kontrolliert die Buttons des Modals, was beim Import oder Erstellen einer Datenbank die vorhandene Datenbank backupen lässt
    @app.callback(
        Output("modalBestätigungImport", "opened", allow_duplicate=True),
        Output("current_db_cache", "data", allow_duplicate=True),
        Output("mainGrid", "rowData", allow_duplicate=True),
        Input("einstellung_datenbank_modal_ja", "n_clicks"),
        Input("einstellung_datenbank_modal_nein", "n_clicks"),
        Input("einstellung_datenbank_modal_abbrechen", "n_clicks"),
        State("current_db_cache", "data"),
    )
    def backup_db_on_import(
        ja_n_clicks, nein_n_clicks, abbrechen_n_clicks, import_data
    ):
        content_encoded = json.loads(import_data)
        content = base64.b64decode(content_encoded)

        if ctx.triggered_id == "einstellung_datenbank_modal_ja":
            functions.backup_db()
            new_db = Path(f"current.sqlite")
            new_db.write_bytes(content)

        elif ctx.triggered_id == "einstellung_datenbank_modal_nein":
            new_db = Path(f"current.sqlite")
            new_db.write_bytes(content)

        elif ctx.triggered_id == "einstellung_datenbank_modal_abbrechen":
            pass

        return (
            False,
            json.dumps(""),
            functions.getMainTable().to_dict("records"),
        )  # Lösche den gespeicherten Cache, um keinen unnötigen Platz zu verbrauchen. Erneuere außerdem die Tabelle, damit direkt der Inhalt der neuen Datenbank angezeigt wird.
