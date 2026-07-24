from dash import Dash, html, dcc
import dash_mantine_components as dmc
import dash_ag_grid as dag
from dash_extensions import EventListener
from dash_iconify import DashIconify
from datetime import datetime, timedelta
import icons


class DateInput(dmc.DateInput):
    """Vorkonfigurierter DateInput mit Button, um das Datum auf Heute zu setzen, von Dash Mantine Components."""

    def __init__(self, id: str, label: str, buttonId: str):
        """
        Args:
            id (str): Id der Komponente
            label (str): Text, der über der Komponente angezeigt werden soll
            buttonId (str): Id des Buttons
        """
        super().__init__(
            id=id,
            label=label,
            valueFormat="DD.MM.YYYY",
            firstDayOfWeek=1,
            monthLabelFormat="MMMM",
            monthsListFormat="MMM",
            weekdayFormat="dd",
            highlightToday=True,
            clearable=True,
            rightSection=dmc.Tooltip(
                dmc.ActionIcon(
                    DashIconify(
                        icon=icons.today,
                        height=16,
                    ),
                    variant="light",
                    id=buttonId,
                    size="md",
                ),
                label="Heute",
            ),
        )


class NumberInput(dmc.NumberInput):
    """Vorkonfigurierter NumberInput von Dash Mantine Components.
    Erlaubt keine negativen Zahlen, blendet Kontrollelemente aus und zeigt immer ein deutsches Komma an.
    """

    def __init__(self, id: str, label: str, **kwargs):
        """Args:
        id (str): Id der Komponente
        label (str): Text, der über der Komponente angezeigt werden soll"""
        super().__init__(
            id=id,
            label=label,
            decimalSeparator=",",
            allowNegative=False,
            allowedDecimalSeparators=[",", "."],
            hideControls=True,
            **kwargs,
        )
