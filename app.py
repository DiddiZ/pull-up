from datetime import datetime
from pathlib import Path

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Dash, Input, Output, callback, dcc, html


class Storage:
    """Simple CSV data torage."""

    def __init__(self, file: Path) -> None:
        """Initialize storage from a CSV file."""
        self.file = file
        if file.exists():
            self.data = pd.read_csv(file, parse_dates=["ts"], index_col="ts", date_format="ISO8601")
        else:
            self.data = pd.DataFrame(columns=["count"], index=pd.DatetimeIndex([], name="ts"))

    def add_pull_ups(self, ts: datetime, count: int) -> None:
        """Add a new pull up entry."""
        self.data = pd.concat([self.data, pd.DataFrame({"count": [count]}, pd.DatetimeIndex([ts], name="ts"))])

    def write(self) -> None:
        """Write data back to CSV file."""
        self.data.to_csv(self.file)

    def did_pull_ups(self, ts: datetime) -> bool:
        """Check if pull ups were done on a given date."""
        return not self.data[self.data.index.date == ts.date()].empty

    def get_last_pull_up(self) -> tuple[datetime, int] | None:
        """Get the last pull up entry."""
        if self.data.empty:
            return None
        return self.data.index.max(), self.data.loc[self.data.index.max(), "count"]

    def pull_ups_for_date(self, date: datetime) -> int:
        """Calculate pull up target for a given date."""
        last = self.get_last_pull_up()
        if last is None:
            return 1

        if last[0].date() >= date.date():
            raise ValueError("Pull ups already recorded for this date")

        days_passed = (date.date() - last[0].date()).days
        return max(last[1] - days_passed, 1)


storage = Storage(Path("pull_ups.csv"))

app = Dash(external_stylesheets=[dbc.themes.SLATE])


app.layout = (
    dbc.Container(
        [
            html.H1("Pull Up Tracker"),
            html.Div(id="pull-up-target"),
            dbc.ButtonGroup([
                dbc.Button("I did it!", color="success", id="success-button"),
            ]),
            dcc.Interval(id="interval-component", interval=1 * 1000, n_intervals=0),  # in milliseconds
        ],
        fluid="sm",
    ),
)


@callback(
    Output("success-button", "disabled"),
    Output("pull-up-target", "children"),
    Input("interval-component", "n_intervals"),
    Input("success-button", "n_clicks"),
)
def update_metrics(*n: int) -> tuple[bool, str]:
    """Update pull up target and button state."""
    if storage.did_pull_ups(datetime.now()):
        return True, "You have already completed your pull ups for today. Great job!"
    return False, f"Your pull up target for today is: {storage.pull_ups_for_date(datetime.now())}"


@callback(
    Input("success-button", "n_clicks"),
    prevent_initial_call=True,
)
def on_success(n_clicks: int) -> None:
    """Handle success button click."""
    storage.add_pull_ups(datetime.now(), storage.pull_ups_for_date(datetime.now()))
    storage.write()


if __name__ == "__main__":
    app.run()

    # if storage.did_pull_ups(datetime.now()):
    #     print("Already did pull ups today")
    # else:
    #     print("Do your pull ups:", storage.pull_ups_for_date(datetime.now()))

    # storage.add_pull_ups(datetime.now() - timedelta(hours=24), 10)
    # if storage.did_pull_ups(datetime.now()):
    #     print("Already did pull ups today")
    # else:
    #     print("Do your pull ups:", storage.pull_ups_for_date(datetime.now()))

    # storage.add_pull_ups(datetime.now(), 10)
    # if storage.did_pull_ups(datetime.now()):
    #     print("Already did pull ups today")
    # else:
    #     print("Do your pull ups:", storage.pull_ups_for_date(datetime.now()))
