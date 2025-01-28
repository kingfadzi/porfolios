import dash_bootstrap_components as dbc
from dash import html

def kpi_layout():
    return dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Total Repos", className="text-center bg-light"),
                        dbc.CardBody(html.H4("0", className="text-center")),
                    ],
                    className="mb-4",
                ),
                width=2
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Avg Commits per Repo", className="text-center bg-light"),
                        dbc.CardBody(html.H4("0", className="text-center")),
                    ],
                    className="mb-4",
                ),
                width=2
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Avg Contributors per Repo", className="text-center bg-light"),
                        dbc.CardBody(html.H4("0", className="text-center")),
                    ],
                    className="mb-4",
                ),
                width=2
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Avg Lines of Code per Repo", className="text-center bg-light"),
                        dbc.CardBody(html.H4("0", className="text-center")),
                    ],
                    className="mb-4",
                ),
                width=2
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Avg CCN", className="text-center bg-light"),
                        dbc.CardBody(html.H4("0", className="text-center")),
                    ],
                    className="mb-4",
                ),
                width=2
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Avg Repo Size", className="text-center bg-light"),
                        dbc.CardBody(html.H4("0", className="text-center")),
                    ],
                    className="mb-4",
                ),
                width=2
            ),
        ],
        className="mb-4",
    )