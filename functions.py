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
)
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.engine import Engine
from sqlalchemy import event
from pathlib import Path
import shutil
import datetime as dt

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

    barcode = Column("Barcode", String(), primary_key=True)
    cas_nr = Column("CAS-Nr", String())
    name = Column("Name", String())
    summenformel = Column("Summenformel", String())
    raum_id = Column("Raum_ID", ForeignKey("räume.Raum_ID"))
    lieferant_id = Column("Lieferant_ID", ForeignKey("lieferanten.Lieferant_ID"))
    füllmenge = Column("Füllmenge", Float())
    mengeneinheit_id = Column(
        "Mengeneinheit_ID", ForeignKey("mengeneinheiten.Mengeneinheit_ID")
    )
    kaufdatum = Column("Kaufdatum", String())
    hersteller_id = Column("Hersteller_ID", ForeignKey("hersteller.Hersteller_ID"))
    reinheit = Column("Reinheit", String())
    konzentration = Column("Konzentration", String())
    lösungsmittel = Column("Lösungsmittel", String())
    molmasse = Column("Molmasse", Float())
    zuletzt_geprüft = Column("Zuletzt_geprüft", String())

    def __repr__(self) -> str:
        return f"User(barcode={self.barcode!r}, cas-nr={self.cas_nr!r}, name={self.name!r}, summenformel={self.summenformel!r}, raum_id={self.raum_id!r}, lieferant_id={self.lieferant_id!r}, füllmenge={self.füllmenge!r}, mengeneinheit_id={self.mengeneinheit_id!r},kaufdatum={self.kaufdatum!r}, hersteller_id={self.hersteller_id!r}, reinheit={self.reinheit!r}, konzentration={self.konzentration!r}, lösungsmittel={self.lösungsmittel!r}, molmasse={self.molmasse!r}, zuletzt_geprüft={self.zuletzt_geprüft!r})"


class Gebäude(Base):
    __tablename__ = "gebäude"

    gebäude_id = Column("Gebäude_ID", Integer, autoincrement=True, primary_key=True)
    gebäude = Column("Gebäude", String())

    def __repr__(self) -> str:
        return f"Gebäude(gebäude_id={self.gebäude_id!r}, gebäude={self.gebäude!r})"


class Gestisdaten(Base):
    __tablename__ = "gestisdaten"

    id = Column("ID", Integer, nullable=False, primary_key=True, autoincrement=True)
    cas_nr = Column("CAS-Nr", String())
    name = Column("Name", String())
    summenformel = Column("Summenformel", String())
    molmasse = Column("Molmasse", Float)
    gestis_link = Column("GESTIS-Link", String())

    def __repr__(self) -> str:
        return f"Gestisdaten(id={self.id!r}, cas_nr={self.cas_nr!r}, name={self.name}, summenformel={self.summenformel}, molmasse={self.molmasse}, gestis_link={self.gestis_link})"


class Hersteller(Base):
    __tablename__ = "hersteller"

    hersteller_id = Column(
        "Hersteller_ID", Integer, autoincrement=True, primary_key=True
    )
    hersteller = Column("Hersteller", String())

    def __repr__(self) -> str:
        return f"Hersteller(hersteller_id={self.hersteller_id!r}, hersteller={self.hersteller!r})"


class Lieferanten(Base):
    __tablename__ = "lieferanten"

    lieferant_id = Column("Lieferant_ID", Integer, autoincrement=True, primary_key=True)
    lieferant = Column("Lieferant", String())

    def __repr__(self) -> str:
        return f"Lieferanten(lieferant_id={self.lieferant_id!r}, lieferant={self.lieferant!r})"


class Mengeneinheiten(Base):
    __tablename__ = "mengeneinheiten"
    mengeneinheit_id = Column(
        "Mengeneinheit_ID", Integer, autoincrement=True, primary_key=True
    )
    mengeneinheit = Column("Mengeneinheit", String())

    def __repr__(self) -> str:
        return f"Mengeneinheiten(mengeneinheit_id={self.mengeneinheit_id!r}, mengeneinheit={self.mengeneinheit!r})"


class Räume(Base):
    __tablename__ = "räume"

    raum_id = Column("Raum_ID", Integer, autoincrement=True, primary_key=True)
    gebäude_id = Column("Gebäude_ID", ForeignKey("gebäude.Gebäude_ID"))
    raum = Column("Raum", String())

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


def selectInInventory(
    barcode: str,
    columnSelect: str,
) -> str:
    """Lese den Wert einer Spalte der Inventartabelle aus, in dessen Zeile der entsprechende Barcode steht."""
    with Session(engine) as session:
        stmt = select(getattr(Inventar, columnSelect)).where(
            Inventar.barcode == barcode
        )
        item = session.scalars(stmt).one_or_none()
        session.close()
    if item is None:
        return ""
    else:
        return str(item)


def deleteInInventory(barcode: str):
    """Lösche den Eintrag mit dem enstprechenden Barcode"""
    with Session(engine) as session:
        entry = session.get(Inventar, barcode)
        session.delete(entry)
        session.commit()
        session.close()
    return


def updateInInventory(
    barcode,
    columnsSelect: list[str],
    values: list[int | float | str],
):
    """Update eine Zeile in der Inventartabelle mit Werten in den entsprechenden Spalten."""
    if len(columnsSelect) != len(values):
        raise ValueError(
            "columnsSelect und values müssen die gleiche Anzahl Elemente besitzen"
        )
    dict = {
        getattr(Inventar, columnsSelect[i]): values[i]
        for i in range(len(columnsSelect))
    }
    for k, v in dict.items():
        if v == "":
            dict.update({k: None})
    with Session(engine) as session:
        session.query(Inventar).filter_by(barcode=barcode).update(dict)
        session.commit()
        session.close()


def createInInventory(
    columnsSelect: list[str],
    values: list[int | float | str | None],
):
    """Erstelle eine neue Zeile in der Inventartabelle mit Werten in den entsprechenden Spalten."""
    if len(columnsSelect) != len(values):
        raise ValueError(
            "columnsSelect und values müssen die gleiche Anzahl Elemente besitzen"
        )

    with Session(engine) as session:
        table = Inventar()
        for i in range(len(columnsSelect)):
            setattr(table, columnsSelect[i], values[i])
        session.add(table)
        session.commit()
        session.close()
    return


def generateSelectData(table: Type[Base], columns: list[str]) -> list[dict]:
    """Generiere eine Liste mit den Auswahlmöglichkeiten für die Dropdown-Selektoren"""
    columnClasses = [getattr(table, column) for column in columns]
    with Session(engine) as session:
        stmt = select(*columnClasses)
        items = session.execute(stmt).all()
        session.close()
    data = [{"value": str(item[0]), "label": str(item[1])} for item in items]
    return data


def generateSelectData_Räume() -> list[dict]:
    """Generiere eine Liste mit den Auswahlmöglichkeiten für die Dropdown-Selektoren für die Räume, die nach den Gebäuden sortiert sein sollen"""
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
    """Generiere eine Liste mit den Auswahlmöglichkeiten für die Dropdown-Selektoren für die Räume, die nach den Gebäuden sortiert sein sollen"""
    with Session(engine) as session:
        stmt1 = select(Inventar.barcode, Inventar.name)
        stmt2 = select(Gestisdaten.id, Gestisdaten.name)
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


def insertStammdaten(selector: str, columns: list[str], values: list[str]):
    if len(columns) == 0:
        raise ValueError("columns mustn't be empty")
    if len(values) == 0:
        raise ValueError("values mustn't be empty")

    table = stammdatenTables[selector]
    with Session(engine) as session:
        table = stammdatenTables[selector]()
        for i in range(len(columns)):
            setattr(table, columns[i].lower(), values[i])
        session.add(table)
        session.commit()
        session.close()
    return


def getMainTable():
    df = pd.read_sql(
        "SELECT `CAS-Nr`, Name, Summenformel, Barcode, Raum FROM inventar INNER JOIN räume ON inventar.Raum_ID == räume.Raum_ID",
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
            "entry is in both the inventory as well as the GESTIS table. Use unique identifiers for both tables!"
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
    dest_path = Path("backup") / (
        dt.datetime.today().isoformat(timespec="seconds") + ".sqlite"
    )
    Path.mkdir(Path("backup"), exist_ok=True)
    shutil.copy(src_path, dest_path)
