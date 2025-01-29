import dash_bootstrap_components as dbc
from dash import html

def kpi_layout():
    return dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            "Total Repos",
                            className="text-center bg-light",
                            style={"fontSize": "0.8rem", "whiteSpace": "nowrap"}
                        ),
                        dbc.CardBody(html.H4("0", id="kpi-total-repos", className="text-center")),
                    ],
                    className="mb-4",
                ),
                width=2
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            "Avg Commits",
                            className="text-center bg-light",
                            style={"fontSize": "0.8rem", "whiteSpace": "nowrap"}
                        ),
                        dbc.CardBody(html.H4("0", id="kpi-avg-commits", className="text-center")),
                    ],
                    className="mb-4",
                ),
                width=2
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            "Avg Contributors",
                            className="text-center bg-light",
                            style={"fontSize": "0.8rem", "whiteSpace": "nowrap"}
                        ),
                        dbc.CardBody(html.H4("0", id="kpi-avg-contributors", className="text-center")),
                    ],
                    className="mb-4",
                ),
                width=2
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            "Avg Lines of Code",
                            className="text-center bg-light",
                            style={"fontSize": "0.8rem", "whiteSpace": "nowrap"}
                        ),
                        dbc.CardBody(html.H4("0", id="kpi-avg-loc", className="text-center")),
                    ],
                    className="mb-4",
                ),
                width=2
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            "Avg CCN",
                            className="text-center bg-light",
                            style={"fontSize": "0.8rem", "whiteSpace": "nowrap"}
                        ),
                        dbc.CardBody(html.H4("0", id="kpi-avg-ccn", className="text-center")),
                    ],
                    className="mb-4",
                ),
                width=2
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            "Avg Repo Size",
                            className="text-center bg-light",
                            style={"fontSize": "0.8rem", "whiteSpace": "nowrap"}
                        ),
                        dbc.CardBody(html.H4("0", id="kpi-avg-repo-size", className="text-center")),
                    ],
                    className="mb-4",
                ),
                width=2
            ),
        ],
        className="mb-4",
    )
