from dash import dcc
import dash_bootstrap_components as dbc

def chart_layout():
    return dbc.Col(
        [
            dcc.Graph(id="active-inactive-bar", config={"displayModeBar": False}, className="mb-4"),
            dcc.Graph(id="classification-pie", config={"displayModeBar": False}, className="mb-4"),
            dcc.Graph(id="heatmap-viz", config={"displayModeBar": False}),
            dcc.Graph(id="repos-by-language-bar", config={"displayModeBar": False}, className="mb-4"),
        ],
        width=9,
    )