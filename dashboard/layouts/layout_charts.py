from dash import dcc, html
import dash_bootstrap_components as dbc

def chart_layout():
    """
    Layout for all charts including the IaC chart.
    """
    return dbc.Col(
        [
            # IaC Chart
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.B("Repositories by IaC Type", className="text-center"),
                        className="bg-light",
                    ),
                    dcc.Graph(
                        id="iac-bar-chart",
                        config={"displayModeBar": False},
                        style={"height": 300},
                    ),
                ],
                className="mb-4",
            ),
            # Active vs Inactive Chart
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.B("Active vs Inactive Repositories", className="text-center"),
                        className="bg-light",
                    ),
                    dcc.Graph(
                        id="active-inactive-bar",
                        config={"displayModeBar": False},
                        style={"height": 300},
                    ),
                ],
                className="mb-4",
            ),
            # Classification Pie Chart
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.B("Repository Classification", className="text-center"),
                        className="bg-light",
                    ),
                    dcc.Graph(
                        id="classification-pie",
                        config={"displayModeBar": False},
                        style={"height": 300},
                    ),
                ],
                className="mb-4",
            ),
            # Language Distribution Chart
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.B("Repositories by Main Language", className="text-center"),
                        className="bg-light",
                    ),
                    dcc.Graph(
                        id="repos-by-language-bar",
                        config={"displayModeBar": False},
                        style={"height": 300},
                    ),
                ],
                className="mb-4",
            ),
            # Heatmap Chart
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.B("Commit Buckets vs Contributor Buckets", className="text-center"),
                        className="bg-light",
                    ),
                    dcc.Graph(
                        id="heatmap-viz",
                        config={"displayModeBar": False},
                        style={"height": 300},
                    ),
                ],
                className="mb-4",
            ),
        ]
    )