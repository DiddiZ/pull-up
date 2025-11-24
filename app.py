from datetime import datetime, timedelta
from pathlib import Path

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
from dash import Dash, Input, Output, callback, dcc, html
from dash_bootstrap_templates import load_figure_template


class Storage:  # TODO: Move to separate file
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
        return max(last[1] + 1 - (days_passed - 1), 1)


storage = Storage(Path("pull_ups.csv"))


load_figure_template("slate")
fig = go.Figure(  # TODO: Move to separate function
    data=go.Scatter(x=storage.data.index, y=storage.data["count"], mode="lines+markers", line=dict(color="#5bc0de")),
)
fig.layout.update(
    xaxis_range=[datetime.now() - timedelta(days=30), datetime.now() + timedelta(days=1)],
    yaxis_range=[0, max(storage.data["count"].max() + 2, 10)],
    margin=dict(l=0, r=0, t=0, b=0),
    height=200,
)

app = Dash(external_stylesheets=[dbc.themes.SLATE], title="Pull-up", update_title=None)
app.layout = (
    dbc.Container(
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.H1("Pull-up Tracker"),
                        html.Hr(className="my-2"),
                        dcc.Graph(figure=fig),  # TODO: Update figure
                        html.Br(),
                        dbc.Button(
                            "Loading...",
                            id="success-button",
                            color="success",
                            size="lg",
                            disabled=True,
                        ),
                    ],
                    className="p-4 bg-primary rounded-3",
                ),
                width=6,
            ),
            justify="center",
        )
    ),
    dcc.Interval(id="interval-component", interval=60 * 1000, n_intervals=0),  # in milliseconds
)


@callback(
    Output("success-button", "disabled"),
    Output("success-button", "children"),
    Input("interval-component", "n_intervals"),
    Input("success-button", "n_clicks"),
)
def update_metrics(*n: int) -> tuple[bool, str]:
    """Update pull up target and button state."""
    if storage.did_pull_ups(datetime.now()):
        return True, "You have already completed your pull ups for today. Great job!"
    return False, f"I did my {storage.pull_ups_for_date(datetime.now())} pull-ups today!"


@callback(
    Input("success-button", "n_clicks"),
    prevent_initial_call=True,
    running=[(Output("success-button", "disabled"), True, False)],
)
def on_success(n_clicks: int) -> None:
    """Handle success button click."""
    storage.add_pull_ups(datetime.now(), storage.pull_ups_for_date(datetime.now()))
    storage.write()


if __name__ == "__main__":
    app.run()
