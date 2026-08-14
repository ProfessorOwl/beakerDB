from dash import Dash, html, dcc
import dash_mantine_components as dmc
import dash_ag_grid as dag
from dash_extensions import EventListener
from dash_iconify import DashIconify
from datetime import datetime, timedelta
import icons
import functions


class DateInput(dmc.DateInput):
    """Vorkonfigurierter DateInput mit Button, um das Datum auf Heute zu setzen."""

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
    """Vorkonfigurierter NumberInput. Erlaubt keine negativen Zahlen, blendet Kontrollelemente aus und zeigt immer ein deutsches Komma an."""

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


class KbdTooltip(dmc.Tooltip):
    """Vorkonfigurierter Tooltip mit mehr padding-bottom"""

    def __init__(self, **kwargs):
        super().__init__(pb=10, position="bottom", **kwargs)


class Version:
    """Component that checks for a new version when initializing"""

    latest_version = functions.get_version_number()
    color = "gray.6"
    badge_children = "Aktuell"

    def __init__(self, version):
        self.current_version = version.removeprefix("Version ")
        if self.latest_version:
            if self.latest_version[0] != "v":
                pass
            elif self.latest_version != self.current_version:
                self.color = "green.3"
                self.badge_children = "Update verfügbar"

    def Badge(self):
        return dmc.Badge(self.badge_children, color=self.color)

    def Text(self):
        return dmc.Text("Version " + self.current_version, c=self.color)
