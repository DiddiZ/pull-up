from datetime import UTC, datetime, timedelta
from pathlib import Path

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
from dash import Dash, Input, Output, callback, dcc, html, no_update
from dash_bootstrap_templates import load_figure_template


class Storage:  # TODO: Move to separate file
    """Simple CSV data torage."""

    def __init__(self, file: Path) -> None:
        """Initialize storage from a CSV file."""
        self.file = file
        if file.exists():
            self.data = pd.read_csv("pull_ups.csv", index_col="ts", date_format="ISO8601")
            self.data.index = pd.to_datetime(self.data.index, format="ISO8601", utc=True)
        else:
            self.data = pd.DataFrame(columns=["count"], index=pd.DatetimeIndex([], name="ts", tz=UTC))

    def add_pull_ups(self, ts: datetime, count: int) -> None:
        """Add a new pull up entry."""
        self.data = pd.concat([self.data, pd.DataFrame({"count": [count]}, pd.DatetimeIndex([ts], name="ts", tz=UTC))])

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


def create_figure() -> go.Figure:
    """Create the pull-up progress figure."""
    fig = go.Figure()

    # Group data by gaps larger than 3 days to create breaks in the line plot
    groups = (storage.data.index.to_series().diff() > timedelta(days=3)).cumsum()
    fig.add_traces([
        go.Scatter(
            x=group.index,
            y=group["count"],
            mode="lines+markers",
            line_color="#5bc0de",
            showlegend=False,
        )
        for _, group in storage.data.groupby(groups)
    ])

    fig.layout.update(
        xaxis_range=[datetime.now(tz=UTC) - timedelta(days=30), datetime.now(tz=UTC) + timedelta(days=1)],
        yaxis_range=[0, max(storage.data["count"].max() + 2, 10)],
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        height=200,
    )
    return fig


app = Dash(external_stylesheets=[dbc.themes.SLATE], title="Pull-up", update_title=None)
app.layout = (
    dbc.Container(
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.H1("Pull-up Tracker"),
                        html.Hr(className="my-2"),
                        dcc.Graph(figure=create_figure(), id="pull-up-graph"),
                        html.Br(),
                        dbc.ButtonGroup(
                            [
                                dbc.Button(
                                    "Loading...",
                                    id="success-button",
                                    color="success",
                                    disabled=True,
                                ),
                                dbc.DropdownMenu(
                                    [dbc.DropdownMenuItem("Loading...", id="i-did-more-button")],
                                    label="",
                                    direction="end",
                                    group=True,
                                    color="primary",
                                ),
                            ],
                            class_name="w-100",
                        ),
                    ],
                    className="p-4 bg-primary rounded-3",
                ),
                md=12,
                lg=8,
                xl=6,
            ),
            justify="center",
        ),
        fluid="md",
    ),
    dcc.Interval(id="interval-component", interval=60 * 1000, n_intervals=0),  # in milliseconds
)


@callback(
    Output("success-button", "disabled"),
    Output("success-button", "children"),
    Output("i-did-more-button", "disabled"),
    Output("i-did-more-button", "children"),
    Output("pull-up-graph", "figure"),
    Input("interval-component", "n_intervals"),
    Input("success-button", "n_clicks"),
    Input("i-did-more-button", "n_clicks"),
)
def update_metrics(*n: int) -> tuple[bool, str, bool, str, go.Figure]:
    """Update pull up target and button state."""
    if storage.did_pull_ups(datetime.now(tz=UTC)):
        _, pull_ups = storage.get_last_pull_up()
        return (
            True,
            "You have already completed your pull ups for today. Great job!",
            False,
            f"I did {pull_ups + 1}",
            create_figure(),
        )
    return (
        False,
        f"I did my {storage.pull_ups_for_date(datetime.now(tz=UTC))} pull-ups today!",
        True,
        "I did more",
        create_figure(),
    )


@callback(
    Input("success-button", "n_clicks"),
    prevent_initial_call=True,
    running=[(Output("success-button", "disabled"), True, no_update)],
)
def on_success(n_clicks: int) -> None:
    """Handle success button click."""
    storage.add_pull_ups(datetime.now(tz=UTC), storage.pull_ups_for_date(datetime.now(tz=UTC)))
    storage.write()


@callback(
    Input("i-did-more-button", "n_clicks"),
    prevent_initial_call=True,
    running=[(Output("i-did-more-button", "disabled"), True, no_update)],
)
def on_i_did_more(n_clicks: int) -> None:
    """Handle i did more button click."""
    _, pull_ups = storage.get_last_pull_up()
    storage.add_pull_ups(datetime.now(tz=UTC), pull_ups + 1)
    storage.write()


if __name__ == "__main__":
    app.run()
