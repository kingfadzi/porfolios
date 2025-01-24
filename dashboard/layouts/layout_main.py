from dash import html
import dash_bootstrap_components as dbc
from layouts.layout_filters import filter_layout
from layouts.layout_charts import chart_layout

def main_layout():
    return dbc.Container(
        [
            html.Div(id="app-layout", style={"display": "none"}),  # Hidden div to trigger callbacks
            html.H1(
                "Custom Dashboard",
                className="bg-secondary text-white p-2 mb-4 text-center",
            ),
            dbc.Row(
                [
                    # Filter Section
                    dbc.Col(filter_layout(), md=3),

                    # Chart/Table Toggle and Display Section
                    dbc.Col(
                        [
                            # Add a toggle for switching between chart and table
                            dbc.RadioItems(
                                id="toggle-view",
                                options=[
                                    {"label": "Visualization", "value": "viz"},
                                    {"label": "Table", "value": "table"},
                                ],
                                value="viz",
                                inline=True,
                                className="mb-3",
                            ),
                            # This will dynamically update between chart and table
                            html.Div(id="chart-or-table"),
                        ],
                        md=9,
                    ),
                ]
            ),
        ],
        fluid=True,
    )