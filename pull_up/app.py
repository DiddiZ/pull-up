from datetime import UTC, datetime, timedelta
from pathlib import Path

import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash import Dash, Input, Output, callback, dcc, html, no_update
from dash_bootstrap_templates import load_figure_template

from pull_up.database import Storage
from pull_up.schedule import IncrementingExerciseSchedule

storage = Storage(Path("pull_ups.csv"))
schedule = IncrementingExerciseSchedule("pull-up")


load_figure_template("slate")


def create_figure() -> go.Figure:
    """Create the pull-up progress figure."""
    fig = go.Figure()

    # Group data by gaps larger than 3 days to create breaks in the line plot
    groups = []
    last_date = None
    for entry in storage.data:
        if last_date is None or (entry.ts - last_date).days > 3:
            groups.append([])
        groups[-1].append(entry)
        last_date = entry.ts

    for group in groups:
        fig.add_trace(
            go.Scatter(
                x=[entry.ts for entry in group],
                y=[entry.count for entry in group],
                mode="lines+markers",
                line_color="#5bc0de",
                name="Pull-ups",
                showlegend=False,
            )
        )

    fig.layout.update(
        xaxis_range=[datetime.now(tz=UTC) - timedelta(days=30), datetime.now(tz=UTC) + timedelta(days=1)],
        yaxis_range=[0, max((storage.get_max_count("pull-up") or 0) + 2, 10)],
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
    output=[
        Output("success-button", "disabled"),
        Output("success-button", "children"),
        Output("i-did-more-button", "disabled"),
        Output("i-did-more-button", "children"),
        Output("pull-up-graph", "figure"),
    ],
    inputs=[
        Input("interval-component", "n_intervals"),
        Input("success-button", "disabled"),
        Input("i-did-more-button", "disabled"),
    ],
)
def update_metrics(*_n: int) -> tuple[bool, str, bool, str, go.Figure]:
    """Update pull up target and button state."""
    today = datetime.now(tz=UTC).date()
    target = schedule.get_target_for_date(storage, today)
    max_count = storage.get_max_count("pull-up", day=today)
    target_reached = max_count is not None and max_count >= target

    return (
        target_reached,
        "You have already completed your pull ups for today. Great job!"
        if target_reached
        else f"I did my {target} pull-ups today!",
        not target_reached,
        "I did more",
        create_figure(),
    )


@callback(
    inputs=[Input("success-button", "n_clicks")],
    running=[(Output("success-button", "disabled"), True, no_update)],
)
def on_success(n_clicks: int) -> None:
    """Handle success button click."""
    if not n_clicks:
        return

    ts = datetime.now(tz=UTC)
    storage.add_set(ts, "pull-up", schedule.get_target_for_date(storage, ts.date()))
    storage.write()


@callback(
    inputs=[Input("i-did-more-button", "n_clicks")],
    running=[(Output("i-did-more-button", "disabled"), True, no_update)],
)
def on_i_did_more(n_clicks: int) -> None:
    """Handle i did more button click."""
    if not n_clicks:
        return

    pull_ups = storage.get_last_set("pull-up")
    storage.add_set(datetime.now(tz=UTC), "pull-up", pull_ups.count + 1)
    storage.write()


if __name__ == "__main__":
    app.run()
