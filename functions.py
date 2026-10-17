import pandas as pd
from sqlalchemy import (
    create_engine,
    ForeignKey,
    Integer,
    select,
    Column,
    update,
    inspect,
    event,
    Text,
    REAL,
)
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.engine import Engine
from pathlib import Path
from os import PathLike

import shutil
import platform
import datetime as dt
import json
import dash_mantine_components as dmc
from github import Github
import requests
import certifi

from i18n import i18n

engine = create_engine("sqlite:///current.sqlite")


def convertErrorToMessage(error: Exception):
    if error is None:
        return ""

    text = str(error)
    if "foreign key" in text.lower():
        if "delete from" in text.lower():
            return "Der Eintrag ist in einer anderen Tabelle in Verwendung und kann daher nicht gelöscht werden."
        if "insert into" in text.lower():
            return "Die referenzierte ID des neuen Eintrages ist noch nicht vergeben. Wähle eine andere ID aus oder erstelle in der entsprechenden Tabelle eine neue."
        if "update" in text.lower():
            return "Die referenzierte ID des aktualisierten Eintrages ist noch nicht vergeben. Wähle eine andere ID aus oder erstelle in der entsprechenden Tabelle eine neue."
    return text


class Fmt:
    """Some string identifiers to format printed text."""

    BOLD_START = "\033[1m"
    END = "\033[0m"
    UNDERLINE = "\033[4m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"


# Sorgt dafür, dass Foreign Keys aktiviert sind, sodass verknüpfte Stammdaten nicht fälschlicherweise gelöscht werden können
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Base(DeclarativeBase):
    pass


# Erstelle jede SQL-Tabelle als Objekt für SQLAlchemy
class Inventory(Base):
    __tablename__ = "inventory"

    barcode = Column("barcode", Text(), primary_key=True)
    cas = Column("cas", Text())
    name = Column("name", Text())
    formular = Column("formular", Text())
    room_id = Column(
        "room_id",
        ForeignKey("rooms.room_id"),
        default=0,
    )
    supplier_id = Column(
        "supplier_id",
        ForeignKey("suppliers.supplier_id"),
        default=0,
    )
    amount = Column("amount", Text())
    unit_id = Column(
        "unit_id",
        ForeignKey(
            "units.unit_id",
        ),
        default=1,
    )
    purchasedate = Column("purchasedate", Text())
    manufacturer_id = Column(
        "manufacturer_id",
        ForeignKey("manufacturers.manufacturer_id"),
        default=0,
    )
    purity = Column("purity", Text())
    concentration = Column("concentration", Text())
    solvent = Column("solvent", Text())
    molarmass = Column("molarmass", REAL())
    lastchecked = Column("lastchecked", Text())
    archived = Column(
        "archived",
        Integer(),
        default=0,
    )
    zvg = Column("ZVG", Integer())

    def __repr__(self) -> str:
        return f"inventory(barcode={self.barcode!r}, cas={self.cas!r}, name={self.name!r}, formular={self.formular!r}, room_id={self.room_id!r}, supplier_id={self.supplier_id!r}, amount={self.amount!r}, unit_id={self.unit_id!r},purchasedate={self.purchasedate!r}, manufacturer_id={self.manufacturer_id!r}, purity={self.purity!r}, concentration={self.concentration!r}, solvent={self.solvent!r}, molarmass={self.molarmass!r}, lastchecked={self.lastchecked!r}), archived={self.archived!r}"


class Buildings(Base):
    __tablename__ = "buildings"

    building_id = Column(
        "building_id", Integer, primary_key=True, nullable=True, doc="ID"
    )
    building = Column("building", Text(), doc=i18n.get("Building"))

    def __repr__(self) -> str:
        return (
            f"buildings(building_id={self.building_id!r}, building={self.building!r})"
        )


class Gestis(Base):
    __tablename__ = "gestis"

    zvg = Column(
        "zvg", Integer(), nullable=False, primary_key=True, doc=i18n.get("ZVG no.")
    )
    cas = Column("cas", Text(), doc=i18n.get("CAS no."))
    name = Column("name", Text(), doc=i18n.get("Name"))
    formular = Column("formular", Text(), doc=i18n.get("Molecular formular"))
    molarmass = Column("molarmass", REAL(), doc=i18n.get("Molar mass"))

    def __repr__(self) -> str:
        return f"gestis(zvg={self.zvg!r}, cas={self.cas!r}, name={self.name}, formular={self.formular}, molarmass={self.molarmass})"


class Manufacturers(Base):
    __tablename__ = "manufacturers"

    manufacturer_id = Column(
        "manufacturer_id", Integer, primary_key=True, nullable=True, doc="ID"
    )
    manufacturer = Column("manufacturer", Text(), doc=i18n.get("Manufacturer"))

    def __repr__(self) -> str:
        return f"manufacturers(manufacturer_id={self.manufacturer_id!r}, manufacturer={self.manufacturer!r})"


class Suppliers(Base):
    __tablename__ = "suppliers"

    supplier_id = Column(
        "supplier_id", Integer, primary_key=True, nullable=True, doc="ID"
    )
    supplier = Column("supplier", Text(), doc=i18n.get("Supplier"))

    def __repr__(self) -> str:
        return (
            f"suppliers(supplier_id={self.supplier_id!r}, supplier={self.supplier!r})"
        )


class Units(Base):
    __tablename__ = "units"

    unit_id = Column("unit_id", Integer, primary_key=True, nullable=True, doc="ID")
    unit = Column("unit", Text(), doc=i18n.get("Unit"))

    def __repr__(self) -> str:
        return f"units(unit_id={self.unit_id!r}, unit={self.unit!r})"


class Rooms(Base):
    __tablename__ = "rooms"

    room_id = Column(
        "room_id",
        Integer,
        primary_key=True,
        nullable=True,
        doc=i18n.get("Room") + " ID",
    )
    building_id = Column(
        "building_id",
        ForeignKey("buildings.building_id"),
        doc=i18n.get("Building") + " ID",
    )
    room = Column("room", Text(), doc=i18n.get("Room"))

    def __repr__(self) -> str:
        return f"Räume(room_id={self.room_id!r}, building_id={self.building_id!r}, room={self.room})"


# Verbinde Strings mit den Objekten der Tabellen
stammdatenTables = {
    "inventory": Inventory,
    "units": Units,
    "buildings": Buildings,
    "suppliers": Suppliers,
    "manufacturers": Manufacturers,
    "rooms": Rooms,
    "gestis": Gestis,
}


def select_value(barcode: str, columnSelect: str, table) -> str:
    """Lese den Wert einer Spalte der Tabelle aus, in dessen Zeile der entsprechende Barcode steht."""
    with Session(engine) as session:
        stmt = select(getattr(table, columnSelect)).where(table.barcode == barcode)
        item = session.scalars(stmt).one_or_none()
        session.close()
    if item is None:
        return ""
    else:
        return str(item)


def delete_entry(barcode: str, table):
    """Lösche den Eintrag mit dem enstprechenden Barcode"""
    with Session(engine) as session:
        entry = session.get(table, barcode)
        session.delete(entry)
        session.commit()
        session.close()
    return


def update_row(
    barcode: str,
    columnsSelect: list[str],
    values: list[None | int | float | str],
    table,
):
    """Update eine Zeile in der Tabelle mit Werten in den entsprechenden Spalten."""
    if len(columnsSelect) != len(values):
        raise ValueError(
            "columnsSelect und values müssen die gleiche Anzahl Elemente besitzen"
        )
    dict = {
        getattr(table, columnsSelect[i]): values[i] for i in range(len(columnsSelect))
    }
    for k, v in dict.items():
        if v == "":
            dict.update({k: None})
    with Session(engine) as session:
        session.query(table).filter_by(barcode=barcode).update(dict)
        session.commit()
        session.close()


def create_row(
    columnsSelect: list[str],
    values: list[int | float | str | None],
    table,
):
    """Erstelle eine neue Zeile in der Tabelle mit Werten in den entsprechenden Spalten."""
    if len(columnsSelect) != len(values):
        raise ValueError(
            "columnsSelect und values müssen die gleiche Anzahl Elemente besitzen"
        )

    with Session(engine) as session:
        for i in range(len(columnsSelect)):
            setattr(table, columnsSelect[i], values[i])
        session.add(table)
        session.commit()
        session.close()
    return


def archive_row(barcode: str, to_archive: bool):
    """Toggles if an entry is archived by setting the column 'archived' to 1 or 0"""
    if to_archive:
        update_row(barcode, ["archived"], [1], Inventory)
    else:
        update_row(barcode, ["archived"], [0], Inventory)
    return


def generateSelectData(table: type[Base], columns: list[str]) -> list[dict]:
    """Generiere eine Liste mit den Auswahlmöglichkeiten für die Dropdown-Selektoren"""
    columnClasses = [getattr(table, column) for column in columns]
    with Session(engine) as session:
        stmt = select(*columnClasses)
        items = session.execute(stmt).all()
        session.close()
    data = [{"value": str(item[0]), "label": str(item[1])} for item in items]
    return data


def generateSelectData_Räume() -> list[dict]:
    """Generiere eine Liste mit den Auswahlmöglichkeiten für die Dropdown-Selektoren für die Räume, die nach den Gebäuden gruppiert sein sollen"""
    with Session(engine) as session:
        stmt1 = select(Rooms.room_id, Rooms.room, Buildings.building).join(
            Buildings, Rooms.building_id == Buildings.building_id
        )
        stmt2 = select(Buildings.building)
        items = session.execute(stmt1).all()
        gebäude = session.execute(stmt2).all()
        session.close()

    data = [{"group": i[0], "items": []} for i in gebäude]
    for dat in data:
        lst = []
        for i in items:
            if i[2] == dat["group"]:
                lst.append({"value": str(i[0]), "label": str(i[1])})
        dat.update({"items": lst})
    return data


def generateSelectData_Namen() -> list[dict]:
    """Generiere eine Liste mit den Auswahlmöglichkeiten für die Dropdown-Selektoren für die Chemikalien. Diese sind nach dem Inventar und der GESTIS-Liste gruppiert."""
    with Session(engine) as session:
        stmt1 = select(Inventory.barcode, Inventory.name)
        stmt2 = select(Gestis.zvg, Gestis.name)
        inventar = session.execute(stmt1).all()
        gestis = session.execute(stmt2).all()
        session.close()
    data = []
    data.append(
        {
            "group": "Im Inventar",
            "items": [
                {"value": str(item[0]), "label": f"{item[1]} ({item[0]})"}
                for item in inventar
            ],
        }
    )
    data.append(
        {
            "group": "In GESTIS",
            "items": [
                {"value": str(item[0]), "label": f"{item[1]} ({item[0]})"}
                for item in gestis
            ],
        }
    )
    return data


def get_table_headings(table: str) -> list[str]:
    """Return the name of every column from a table"""
    return stammdatenTables[table].__table__.columns.keys()


def updateStammdaten(selector: str, columns: list[str], values: list[str]):
    """Updates the stammdaten table specified with selector, where ``columns[0] == values[0]``

    :param selector: One of the available tables in the stammdaten table, at the moment: "buildings", "gestis", "manufacturers", "suppliers", "units" and "rooms"
    :type selector: "buildings", "gestis", "manufacturers", "suppliers", "units", "rooms"
    :param columns: A list of column names to update in the selected table
    :type columns: list[str]
    :param values: A list of values to update in the selected table, where the index of ``values`` corresponds to the index of ``columns``
    :type values: list[str]

    :raises ValueError: If columns or values is empty,
    """
    if len(columns) == 0:
        raise ValueError("columns mustn't be empty")
    if len(values) == 0:
        raise ValueError("values mustn't be empty")

    table = stammdatenTables[selector]
    stmt = (
        update(table)
        .where(getattr(table, columns[0].lower()) == values[0])
        .values({columns[i].lower(): values[i] for i in range(1, len(columns))})
    )
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()
        session.close()
    return


def deleteStammdaten(selector: str, values: list[str]):
    """Deletes a row from the stammdaten table specified with selector."""
    if len(values) == 0:
        raise ValueError("values mustn't be empty")

    table = stammdatenTables[selector]
    with Session(engine) as session:
        entry = session.get(table, values[0])
        session.delete(entry)
        session.commit()
        session.close()
    return


def insertStammdaten(selector: str | type[Base], columns: list[str], values: list[str]):
    if len(columns) == 0:
        raise ValueError("columns mustn't be empty")
    if len(values) == 0:
        raise ValueError("values mustn't be empty")

    if isinstance(selector, str):
        table = stammdatenTables[selector]()
    else:
        table = selector()
    with Session(engine) as session:
        for i in range(len(columns)):
            setattr(table, columns[i].lower(), values[i])
        session.add(table)
        session.commit()
        session.close()
    return


def get_main_table(is_archived: bool = False):
    def query(is_archived: int):
        return f"SELECT cas, name, formular, barcode, room, lastchecked FROM inventory INNER JOIN rooms ON inventory.room_id == rooms.room_id WHERE archived == {is_archived} "

    if is_archived:
        df = pd.read_sql(
            query(1),
            "sqlite:///current.sqlite",
            dtype_backend="pyarrow",
        )
    else:
        df = pd.read_sql(
            query(0),
            "sqlite:///current.sqlite",
            dtype_backend="pyarrow",
        )

    return df


def getExistingData(id: str) -> dict[str, str]:
    """Retrieves key-value pairs of a row matching to ``id`` in either the GESTIS table or inventory

    :param id: A unique primary key from inventory or GESTIS table
    :type id: str
    :return: A dict with key-value pairs of every column and its respective value in the searched for row
    :rtype: dict
    """

    with Session(engine) as session:
        entryGestis = session.get(Gestis, id)
        entryInventory = session.get(Inventory, id)

    if entryGestis and entryInventory:
        raise LookupError(
            "Entry is in both the inventory as well as the GESTIS table. Use unique identifiers for both tables!"
        )

    entry = entryGestis or entryInventory
    if entry == None:
        raise TypeError
    mapper = inspect(entry.__class__)

    tableAsDict = dict()
    for i in mapper.column_attrs:
        tableAsDict.update({i.key: str(getattr(entry, i.key))})
    return tableAsDict


def backup_db():
    """Kopiere die Datenbank in den Backup-Ordner"""
    src_path = Path("current.sqlite")
    time = dt.datetime.today().isoformat(timespec="seconds")
    time = time.replace(":", "")
    dest_path = Path("backup") / (time + ".sqlite")
    Path.mkdir(Path("backup"), exist_ok=True)
    shutil.copy(src_path, dest_path)


def save_füllmenge(barcode, date, füllmenge):
    füllmenge_data = []
    füllmenge_raw = select_value(barcode, "amount", Inventory)
    if len(füllmenge_raw or []) != 0 and füllmenge_raw:
        füllmenge_history = json.loads(füllmenge_raw)
        if [date, füllmenge] != füllmenge_history[-1]:
            füllmenge_history.append([date, füllmenge])
        füllmenge_data = [i[1] for i in füllmenge_history]
        füllmenge_history = json.dumps(füllmenge_history)
    elif füllmenge:
        füllmenge_history = [[date, füllmenge]]
        füllmenge_history = json.dumps(füllmenge_history)
    else:
        füllmenge_history = None
    return füllmenge_history, füllmenge_data


def get_füllmenge_data(barcode):
    with Session(engine) as session:
        stmt = select(Inventory.amount).where(Inventory.barcode == barcode)
        füllmenge = json.loads(session.scalars(stmt).one_or_none() or "")

        data = [{"date": i[0], i18n.get("Amount"): i[1]} for i in füllmenge]
        return data


# Declare the function key for Windows (ctrl) and Mac (command) depending on the OS for use in keyboard shortcuts
def system_key() -> dmc.Kbd:
    """Returns either `dmc.Kbd("⌘")` or `dmc.Kbd("Strg")` depending on the system"""
    if platform.system() == "Darwin":
        return dmc.Kbd("⌘")
    else:
        return dmc.Kbd("Strg")


def get_version_number() -> str | None:
    """Returns the version number of the latest release in the beakerDB repository"""
    g = Github(None)
    try:
        if g.get_rate_limit().rate.remaining > 0:
            repo = g.get_repo("ProfessorOwl/beakerDB")
            latest = repo.get_latest_release().name
        else:
            latest = None
    except:
        latest = None
    return latest


def import_gestis(path_to_xlsx: str | PathLike, lang: str):
    """Replaces all the enties in the table ``gestis`` with entries from the imported ``.xlsx``

    Args:
        path_to_xlsx (str | PathLike): Path to the ``.xlsx`` file that can be downloaded on the GESTIS website
        lang (str): Either "de" for the german or "en" for the english table
    """
    df = pd.read_excel(path_to_xlsx)

    # Drop rows "related CAS No", "INDEX No", "EC No", "related EC No", "Linksyntax", "Hyperlink"
    df = df.drop(
        [
            df.columns[2],
            df.columns[3],
            df.columns[4],
            df.columns[5],
            df.columns[9],
            df.columns[10],
        ],
        axis="columns",
    )
    df = df.rename(
        columns={
            df.columns[0]: "zvg",
            df.columns[1]: "cas",
            df.columns[2]: "name",
            df.columns[3]: "formular",
            df.columns[4]: "molarmass",
        }
    )
    df = df.set_index("zvg")

    for i, value in df["molarmass"].items():
        try:
            df.at[i, "molarmass"] = float(value)
        except:
            df.at[i, "molarmass"] = None

    df["molarmass"] = df["molarmass"].apply(pd.to_numeric)

    df["formular"] = [str(i).replace("\n", ", ") for i in df["formular"]]
    for i, value in df["formular"].items():
        if value.strip() == "" or value == "." or value.lower() == "nan":
            df.at[i, "formular"] = None
    df.to_sql("gestis", engine, if_exists="delete_rows")


def init_app(lang: str):
    """Create an empty database and import data from GESTIS. GESTIS data is imported again each time the app gets launched

    Args:
        lang (str): Accepts either "de" or "en" for defining the language of the app and the imported GESTIS-table
    """

    if not Path.exists(Path("current.sqlite")):
        # Dispose of the old engine and create a new one so that old information gets deleted. This is important for importing or creating new databases in the settings of the app
        global engine
        engine.dispose()
        engine = create_engine("sqlite:///current.sqlite")

        # Create an empty table
        Base.metadata.create_all(engine)

        # --- BEGIN Insert basic master data ---
        insertStammdaten(
            Buildings, ["building_id", "building"], ["0", i18n.get("None")]
        )
        insertStammdaten(
            Manufacturers,
            ["manufacturer_id", "manufacturer"],
            ["0", i18n.get("Nothing selected")],
        )
        insertStammdaten(
            Suppliers,
            ["supplier_id", "supplier"],
            ["0", i18n.get("Nothing selected")],
        )
        insertStammdaten(
            Rooms,
            ["room_id", "building_id", "building"],
            ["0", "0", i18n.get("Nothing selected")],
        )
        insertStammdaten(Units, ["unit_id", "unit"], ["1", "g"])
        insertStammdaten(Units, ["unit_id", "unit"], ["2", "mL"])
        # --- END ---

    # --- BEGIN Retrieve GESTIS tables and add one of them to the master data according to lang ---
    gestis_links = {
        "de": "https://www.dguv.de/medien/ifa/de/gestis/stoffdb/links/zvg-cas-list-d.xlsx",
        "en": "https://www.dguv.de/medien/ifa/en/gestis/stoffdb/links/zvg-cast-list-e.xlsx",
    }

    filename = "gestis_" + lang + ".xlsx"
    try:
        content = requests.get(
            gestis_links[lang],
            verify=certifi.where(),
        ).content
    except:
        if Path.exists(Path(filename)):
            print(
                f"{Fmt.BOLD_START}{Fmt.YELLOW}Warning:{Fmt.END} Cannot connect to {gestis_links[lang]} to update the existing GESTIS database."
            )
            return
        else:
            raise ConnectionError(
                f"Cannot connect to {gestis_links[lang]}. No existing GESTIS database found. Either download the missing database from {gestis_links[lang]} and rename it to {filename} or set up the server with a working internet connection."
            )
    try:
        file = open(filename, "xb")
    except FileExistsError:
        file = open(filename, "wb")

    file.write(content)
    file.close()

    import_gestis("gestis_de.xlsx" if lang == "de" else "gestis_en.xlsx", lang)
    # --- END
