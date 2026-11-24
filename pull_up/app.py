from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash import Dash, Input, Output, callback, dcc, html, no_update
from dash_bootstrap_templates import load_figure_template

from pull_up.database import Storage
from pull_up.schedule import ExerciseSchedule, IncrementingExerciseSchedule

storage = Storage(Path("pull_ups.csv"))


@dataclass(frozen=True)
class Exercise:
    """An exercise and associated information."""

    name: str
    unit: str

    @property
    def identifier(self) -> str:
        """A CSS-friendly identifier for the exercise."""
        return self.name.lower().replace(" ", "-")


exercises: list[Exercise] = [
    Exercise("pull-up", "reps"),
]
schedules: dict[str, ExerciseSchedule] = {
    "pull-up": IncrementingExerciseSchedule("pull-up"),
}


load_figure_template("slate")


def create_figure(exercise: Exercise) -> go.Figure:
    """Create the pull-up progress figure."""
    fig = go.Figure()

    # Group data by gaps larger than 3 days to create breaks in the line plot
    groups = []
    last_date = None
    for entry in storage.get_sets(exercise=exercise.name):
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
                name="count",
                showlegend=False,
            )
        )

    fig.layout.update(
        xaxis_range=[datetime.now(tz=UTC) - timedelta(days=30), datetime.now(tz=UTC) + timedelta(days=1)],
        yaxis_range=[0, max((storage.get_max_count(exercise.name) or 0) + 2, 10)],
        yaxis_title=exercise.unit,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        height=200,
    )
    return fig


app = Dash(external_stylesheets=[dbc.themes.SLATE], title="Pull-up", update_title=None)
app.layout = (
    dbc.Container(
        [
            dbc.Row(
                html.Div([
                    html.H1("Exercise Tracker"),
                    html.Hr(className="my-2"),
                ])
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.H2(exercise.name.capitalize()),
                                dcc.Graph(figure=create_figure(exercise), id=f"{exercise.identifier}-graph"),
                                html.Br(),
                                dbc.ButtonGroup(
                                    [
                                        dbc.Button(
                                            "Loading...",
                                            id=f"{exercise.identifier}-success-button",
                                            color="success",
                                            disabled=True,
                                        ),
                                        dbc.DropdownMenu(
                                            [
                                                dbc.DropdownMenuItem(
                                                    "Loading...", id=f"{exercise.identifier}-more-button"
                                                )
                                            ],
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
                        md=6,
                    )
                    for exercise in exercises
                ],
                justify="center",
            ),
        ],
        fluid="md",
    ),
    dcc.Interval(id="interval-component", interval=60 * 1000, n_intervals=0),  # in milliseconds
)


def create_callbacks(exercise: Exercise) -> None:
    """Create callbacks for the given exercise."""

    @callback(
        output=[
            Output(f"{exercise.identifier}-success-button", "disabled"),
            Output(f"{exercise.identifier}-success-button", "children"),
            Output(f"{exercise.identifier}-more-button", "disabled"),
            Output(f"{exercise.identifier}-more-button", "children"),
            Output(f"{exercise.identifier}-graph", "figure"),
        ],
        inputs=[
            Input("interval-component", "n_intervals"),
            Input(f"{exercise.identifier}-success-button", "disabled"),
            Input(f"{exercise.identifier}-more-button", "disabled"),
        ],
    )
    def update_metrics(*_n: int) -> tuple[bool, str, bool, str, go.Figure]:
        """Update pull up target and button state."""
        today = datetime.now(tz=UTC).date()
        target = schedules[exercise.name].get_target_for_date(storage, today)
        max_count = storage.get_max_count(exercise.name, day=today)
        target_reached = max_count is not None and max_count >= target

        return (
            target_reached,
            "You have already reached your goal for today. Great job!"
            if target_reached
            else f"I did my {target} {exercise.unit} today!",
            not target_reached,
            "I did more",
            create_figure(exercise),
        )

    @callback(
        inputs=[Input(f"{exercise.identifier}-success-button", "n_clicks")],
        running=[(Output(f"{exercise.identifier}-success-button", "disabled"), True, no_update)],
    )
    def on_success(n_clicks: int) -> None:
        """Handle success button click."""
        if not n_clicks:
            return

        ts = datetime.now(tz=UTC)
        storage.add_set(ts, exercise.name, schedules[exercise.name].get_target_for_date(storage, ts.date()))
        storage.write()

    @callback(
        inputs=[Input(f"{exercise.identifier}-more-button", "n_clicks")],
        running=[(Output(f"{exercise.identifier}-more-button", "disabled"), True, no_update)],
    )
    def on_i_did_more(n_clicks: int) -> None:
        """Handle i did more button click."""
        if not n_clicks:
            return

        last_set = storage.get_last_set(exercise.name)
        assert last_set is not None
        storage.add_set(datetime.now(tz=UTC), exercise.name, last_set.count + 1)
        storage.write()


for exercise in exercises:
    create_callbacks(exercise)

if __name__ == "__main__":
    app.run()
