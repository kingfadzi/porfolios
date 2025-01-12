from dash import dcc
import dash_bootstrap_components as dbc

def chart_layout():
    return dbc.Col(
        [
            dbc.Card(
                dbc.CardBody([
                    dcc.Graph(
                        id="active-inactive-bar",
                        config={
                            "displayModeBar": True,
                            "displaylogo": False,  # Remove Plotly logo
                            "modeBarButtonsToRemove": ["zoom2d", "pan2d", "select2d", "lasso2d"],
                        },
                    ),
                ]),
                className="mb-4",
            ),
            dbc.Card(
                dbc.CardBody([
                    dcc.Graph(
                        id="classification-pie",
                        config={
                            "displayModeBar": True,
                            "displaylogo": False,  # Remove Plotly logo
                            "modeBarButtonsToRemove": ["zoom2d", "pan2d", "select2d", "lasso2d"],
                        },
                    ),
                ]),
                className="mb-4",
            ),
            dbc.Card(
                dbc.CardBody([
                    dcc.Graph(
                        id="repos-by-language-bar",
                        config={
                            "displayModeBar": True,
                            "displaylogo": False,  # Remove Plotly logo
                            "modeBarButtonsToRemove": ["zoom2d", "select2d", "lasso2d"],  # Allow panning
                        },
                    ),
                ]),
                className="mb-4",
            ),
            dbc.Card(
                dbc.CardBody([
                    dcc.Graph(
                        id="heatmap-viz",
                        config={
                            "displayModeBar": True,
                            "displaylogo": False,  # Remove Plotly logo
                            "modeBarButtonsToRemove": ["zoom2d", "pan2d", "select2d", "lasso2d"],
                        },
                    ),
                ]),
                className="mb-4",
            ),
        ],
        width=9,
    )