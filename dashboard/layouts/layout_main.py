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
                    dbc.Col(filter_layout(), md=3),
                    dbc.Col(chart_layout(), md=9),  # No arguments needed
                ]
            ),
        ],
        fluid=True,
    )