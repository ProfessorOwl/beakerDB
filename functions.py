import pandas as pd
from typing import Type
from sqlalchemy import (
    create_engine,
    ForeignKey,
    String,
    Float,
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
class Inventar(Base):
    __tablename__ = "inventar"

    barcode = Column("Barcode", Text(), primary_key=True)
    cas = Column("CAS", Text())
    name = Column("Name", Text())
    summenformel = Column("Summenformel", Text())
    raum_id = Column(
        "Raum_ID",
        ForeignKey("räume.Raum_ID"),
        default=0,
    )
    lieferant_id = Column(
        "Lieferant_ID",
        ForeignKey("lieferanten.Lieferant_ID"),
        default=0,
    )
    füllmenge = Column("Füllmenge", Text())
    mengeneinheit_id = Column(
        "Mengeneinheit_ID",
        ForeignKey(
            "mengeneinheiten.Mengeneinheit_ID",
        ),
        default=1,
    )
    kaufdatum = Column("Kaufdatum", Text())
    hersteller_id = Column(
        "Hersteller_ID",
        ForeignKey("hersteller.Hersteller_ID"),
        default=0,
    )
    reinheit = Column("Reinheit", Text())
    konzentration = Column("Konzentration", Text())
    lösungsmittel = Column("Lösungsmittel", Text())
    molmasse = Column("Molmasse", REAL())
    zuletzt_geprüft = Column("Zuletzt_geprüft", Text())
    archiviert = Column(
        "Archiviert",
        Integer(),
        default=0,
    )
    zvg = Column("ZVG", Integer())

    def __repr__(self) -> str:
        return f"Inventar(barcode={self.barcode!r}, cas={self.cas!r}, name={self.name!r}, summenformel={self.summenformel!r}, raum_id={self.raum_id!r}, lieferant_id={self.lieferant_id!r}, füllmenge={self.füllmenge!r}, mengeneinheit_id={self.mengeneinheit_id!r},kaufdatum={self.kaufdatum!r}, hersteller_id={self.hersteller_id!r}, reinheit={self.reinheit!r}, konzentration={self.konzentration!r}, lösungsmittel={self.lösungsmittel!r}, molmasse={self.molmasse!r}, zuletzt_geprüft={self.zuletzt_geprüft!r}), archiviert={self.archiviert!r}"


class Gebäude(Base):
    __tablename__ = "gebäude"

    gebäude_id = Column("Gebäude_ID", Integer, primary_key=True, nullable=True)
    gebäude = Column("Gebäude", Text())

    def __repr__(self) -> str:
        return f"Gebäude(gebäude_id={self.gebäude_id!r}, gebäude={self.gebäude!r})"


class Gestisdaten(Base):
    __tablename__ = "gestisdaten"

    zvg = Column("ZVG", Integer(), nullable=False, primary_key=True)
    cas = Column("CAS", Text())
    name = Column("Name", Text())
    summenformel = Column("Summenformel", Text())
    molmasse = Column("Molmasse", REAL())

    def __repr__(self) -> str:
        return f"Gestisdaten(zvg={self.zvg!r}, cas={self.cas!r}, name={self.name}, summenformel={self.summenformel}, molmasse={self.molmasse})"


class Hersteller(Base):
    __tablename__ = "hersteller"

    hersteller_id = Column("Hersteller_ID", Integer, primary_key=True, nullable=True)
    hersteller = Column("Hersteller", Text())

    def __repr__(self) -> str:
        return f"Hersteller(hersteller_id={self.hersteller_id!r}, hersteller={self.hersteller!r})"


class Lieferanten(Base):
    __tablename__ = "lieferanten"

    lieferant_id = Column("Lieferant_ID", Integer, primary_key=True, nullable=True)
    lieferant = Column("Lieferant", Text())

    def __repr__(self) -> str:
        return f"Lieferanten(lieferant_id={self.lieferant_id!r}, lieferant={self.lieferant!r})"


class Mengeneinheiten(Base):
    __tablename__ = "mengeneinheiten"
    mengeneinheit_id = Column(
        "Mengeneinheit_ID", Integer, primary_key=True, nullable=True
    )
    mengeneinheit = Column("Mengeneinheit", Text())

    def __repr__(self) -> str:
        return f"Mengeneinheiten(mengeneinheit_id={self.mengeneinheit_id!r}, mengeneinheit={self.mengeneinheit!r})"


class Räume(Base):
    __tablename__ = "räume"

    raum_id = Column("Raum_ID", Integer, primary_key=True, nullable=True)
    gebäude_id = Column("Gebäude_ID", ForeignKey("gebäude.Gebäude_ID"))
    raum = Column("Raum", Text())

    def __repr__(self) -> str:
        return f"Räume(raum_id={self.raum_id!r}, gebäude_id={self.gebäude_id!r}, raum={self.raum})"


# Verbinde Strings mit den Objekten der Tabellen
stammdatenTables = {
    "inventar": Inventar,
    "mengeneinheiten": Mengeneinheiten,
    "gebäude": Gebäude,
    "lieferanten": Lieferanten,
    "hersteller": Hersteller,
    "räume": Räume,
    "gestisdaten": Gestisdaten,
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
    """Toggles if an entry is archived by setting the column 'Archiviert' to 1 or 0"""
    if to_archive:
        update_row(barcode, ["archiviert"], [1], Inventar)
    else:
        update_row(barcode, ["archiviert"], [0], Inventar)
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
        stmt1 = select(Räume.raum_id, Räume.raum, Gebäude.gebäude).join(
            Gebäude, Räume.gebäude_id == Gebäude.gebäude_id
        )
        stmt2 = select(Gebäude.gebäude)
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
        stmt1 = select(Inventar.barcode, Inventar.name)
        stmt2 = select(Gestisdaten.zvg, Gestisdaten.name)
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


def getHeadings(table: str) -> list[str]:
    """Gebe die Spaltenüberschriften einer Tabelle zurück."""
    return stammdatenTables[table].__table__.columns.keys()


def updateStammdaten(selector: str, columns: list[str], values: list[str]):
    """Updates the stammdaten table specified with selector, where ``columns[0] == values[0]``

    :param selector: One of the available tables in the stammdaten table, at the moment: "Gebäude", "Gestisdaten", "Hersteller", "Lieferanten", "Mengeneinheiten" and "Räume"
    :type selector: "Gebäude", "Gestisdaten", "Hersteller", "Lieferanten", "Mengeneinheiten", "Räume"
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
        return f"SELECT CAS, Name, Summenformel, Barcode, Raum, Zuletzt_geprüft FROM Inventar INNER JOIN räume ON Inventar.Raum_ID == räume.Raum_ID WHERE Archiviert == {is_archived} "

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
        entryGestis = session.get(Gestisdaten, id)
        entryInventory = session.get(Inventar, id)

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
    füllmenge_raw = select_value(barcode, "füllmenge", Inventar)
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
        stmt = select(Inventar.füllmenge).where(Inventar.barcode == barcode)
        füllmenge = json.loads(session.scalars(stmt).one_or_none() or "")

        data = [{"datum": i[0], "Füllmenge": i[1]} for i in füllmenge]
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
    except:
        latest = None
    return latest


def import_gestis(path_to_xlsx: str | PathLike, lang: str):
    """Replaces all the enties in the table ``gestisdaten`` with entries from the imported ``.xlsx``

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
            df.columns[0]: "ZVG",
            df.columns[1]: "CAS",
            df.columns[3]: "Summenformel",
            df.columns[4]: "Molmasse",
        }
    )
    df = df.set_index("ZVG")

    for i, value in df["Molmasse"].items():
        try:
            df.at[i, "Molmasse"] = float(value)
        except:
            df.at[i, "Molmasse"] = None

    df["Molmasse"] = df["Molmasse"].apply(pd.to_numeric)

    df["Summenformel"] = [str(i).replace("\n", ", ") for i in df["Summenformel"]]
    for i, value in df["Summenformel"].items():
        if value.strip() == "" or value == "." or value.lower() == "nan":
            df.at[i, "Summenformel"] = None

    df.to_sql("gestisdaten", engine, if_exists="delete_rows")


def init_app(lang: str):
    """Create an empty database and import data from GESTIS

    Args:
        lang (str): Accepts either "de" or "en" for defining the language of the imported GESTIS-table
    """

    if not Path.exists(Path("current.sqlite")):
        # Create an empty table
        Base.metadata.create_all(engine)

        # --- BEGIN Insert basic master data ---
        insertStammdaten(Gebäude, ["Gebäude_ID", "Gebäude"], ["0", "Ohne"])
        insertStammdaten(
            Hersteller, ["Hersteller_ID", "Hersteller"], ["0", "Nichts ausgewählt"]
        )
        insertStammdaten(
            Lieferanten, ["Lieferant_ID", "Lieferant"], ["0", "Nichts ausgewählt"]
        )
        insertStammdaten(
            Räume, ["Raum_ID", "Gebäude_ID", "Raum"], ["0", "0", "Nichts ausgewählt"]
        )
        insertStammdaten(
            Mengeneinheiten, ["Mengeneinheit_ID", "Mengeneinheit"], ["1", "g"]
        )
        insertStammdaten(
            Mengeneinheiten, ["Mengeneinheit_ID", "Mengeneinheit"], ["2", "mL"]
        )
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


if __name__ == "__main__":
    init_app("de")
