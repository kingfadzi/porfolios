from dash import html
import dash_bootstrap_components as dbc
from layouts.layout_filters import filter_layout
from layouts.layout_charts import chart_layout
from layouts.layout_kpi import kpi_layout

def main_layout():
    return dbc.Container(
        [
            html.Div(id="app-layout", style={"display": "none"}),
            html.H1("Custom Dashboard", className="bg-secondary text-white p-2 mb-4 text-center"),

            # KPI row with placeholder stats
            kpi_layout(),

            # Main row with filters on the left and charts on the right
            dbc.Row(
                [
                    dbc.Col(filter_layout(), md=3),
                    dbc.Col(chart_layout(), md=9),
                ]
            ),
        ],
        fluid=True,
    )
