from dash import dcc, html
import dash_bootstrap_components as dbc

def filter_layout():
    return dbc.Col(
        [
            html.Label("Filter by Host Name:", className="form-label"),
            dcc.Dropdown(
                id="host-name-filter",
                options=[],  # Empty options, will be populated dynamically
                multi=True,
                placeholder="Select Host Name(s)",
                className="form-select mb-3",
            ),
            html.Label("Filter by Main Language:", className="form-label"),
            dcc.Dropdown(
                id="language-filter",
                options=[],  # Empty options, will be populated dynamically
                multi=True,
                placeholder="Select Language(s)",
                className="form-select mb-3",
            ),
            html.Label("Filter by Classification:", className="form-label"),
            dcc.Dropdown(
                id="classification-filter",
                options=[],  # Empty options, will be populated dynamically
                multi=True,
                placeholder="Select Classification(s)",
                className="form-select mb-3",
            ),
        ],
        width=3,
    )