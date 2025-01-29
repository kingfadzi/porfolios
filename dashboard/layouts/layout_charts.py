from dash import dcc, html
import dash_bootstrap_components as dbc

def chart_layout():
    return dbc.Col(
        [
            # Row: Activity Status & Repository Classification
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.B("Repo Status", className="text-center"),
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
                        width=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.B("Repository Sizes", className="text-center"),
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
                        width=6,
                    ),
                ],
                className="mb-4",
            ),

            # Contributors vs Commits Scatter Plot
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.B("Code Contribution Activity", className="text-center"),
                        className="bg-light",
                    ),
                    dcc.Graph(
                        id="scatter-plot",
                        config={"displayModeBar": False},
                        style={"height": 300},
                    ),
                ],
                className="mb-4",
            ),

            # Repositories by Main Language
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.B("Repositories Count by Main Language", className="text-center"),
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

            # Row: Language Usage Buckets & Repository Activity by Last Commit Date
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.B("Num of Languages Use per repod", className="text-center"),
                                    className="bg-light",
                                ),
                                dcc.Graph(
                                    id="language-usage-buckets-bar",
                                    config={"displayModeBar": False},
                                    style={"height": 300},
                                ),
                            ],
                            className="mb-4",
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.B("Last Commit Date", className="text-center"),
                                    className="bg-light",
                                ),
                                dcc.Graph(
                                    id="last-commit-buckets-bar",
                                    config={"displayModeBar": False},
                                    style={"height": 300},
                                ),
                            ],
                            className="mb-4",
                        ),
                        width=6,
                    ),
                ],
                className="mb-4",
            ),

            # CLOC Metrics by Language
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.B("Total Lines of Code per Languagee", className="text-center"),
                        className="bg-light",
                    ),
                    dcc.Graph(
                        id="cloc-bar-chart",
                        config={"displayModeBar": False},
                        style={"height": 300},
                    ),
                ],
                className="mb-4",
            ),

            # Repositories by IaC Type
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.B("infrastructure as Code Usage", className="text-center"),
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

            # Programming Languages vs Contributor Buckets Heatmap
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.B("Code Contribution by Language", className="text-center"),
                        className="bg-light",
                    ),
                    dcc.Graph(
                        id="language-contributors-heatmap",
                        config={"displayModeBar": False},
                        style={"height": 600},
                    ),
                ],
                className="mb-4",
            ),

            # Row: Vulnerabilities by Severity & Standards Issues
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.B("Vulnerabilities by Severity (Shallow scan)", className="text-center"),
                                    className="bg-light",
                                ),
                                dcc.Graph(
                                    id="trivy-vulnerabilities-bar-chart",
                                    config={"displayModeBar": False},
                                    style={"height": 300},
                                ),
                            ],
                            className="mb-4",
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.B("Standards Issues", className="text-center"),
                                    className="bg-light",
                                ),
                                dcc.Graph(
                                    id="semgrep-findings-bar-chart",
                                    config={"displayModeBar": False},
                                    style={"height": 300},
                                ),
                            ],
                            className="mb-4",
                        ),
                        width=6,
                    ),
                ],
                className="mb-4",
            ),

            # Row 1: Java Versions & Build Tools
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(
                            html.B("Java Versions", className="text-center"),
                            className="bg-light",
                        ),
                        dcc.Graph(
                            id="label-tech-bar-chart-java-version",
                            config={"displayModeBar": False},
                            style={"height": 300},
                        ),
                    ], className="mb-4"),
                    width=6
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(
                            html.B("Build Tools", className="text-center"),
                            className="bg-light",
                        ),
                        dcc.Graph(
                            id="label-tech-bar-chart-build-tool",
                            config={"displayModeBar": False},
                            style={"height": 300},
                        ),
                    ], className="mb-4"),
                    width=6
                ),
            ], className="mb-4"),

            # Row 2: Application Servers & Databases
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(
                            html.B("Application Servers", className="text-center"),
                            className="bg-light",
                        ),
                        dcc.Graph(
                            id="label-tech-bar-chart-appserver",
                            config={"displayModeBar": False},
                            style={"height": 300},
                        ),
                    ], className="mb-4"),
                    width=6
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(
                            html.B("Databases", className="text-center"),
                            className="bg-light",
                        ),
                        dcc.Graph(
                            id="label-tech-bar-chart-database",
                            config={"displayModeBar": False},
                            style={"height": 300},
                        ),
                    ], className="mb-4"),
                    width=6
                ),
            ], className="mb-4"),

            # Row 3: Spring Framework & Spring Boot
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(
                            html.B("Spring Framework", className="text-center"),
                            className="bg-light",
                        ),
                        dcc.Graph(
                            id="label-tech-bar-chart-spring-framework-version",
                            config={"displayModeBar": False},
                            style={"height": 300},
                        ),
                    ], className="mb-4"),
                    width=6
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(
                            html.B("Spring Boot", className="text-center"),
                            className="bg-light",
                        ),
                        dcc.Graph(
                            id="label-tech-bar-chart-spring-boot-version",
                            config={"displayModeBar": False},
                            style={"height": 300},
                        ),
                    ], className="mb-4"),
                    width=6
                ),
            ], className="mb-4"),

            # Row 4: Middleware & Logging
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(
                            html.B("Middleware", className="text-center"),
                            className="bg-light",
                        ),
                        dcc.Graph(
                            id="label-tech-bar-chart-middleware",
                            config={"displayModeBar": False},
                            style={"height": 300},
                        ),
                    ], className="mb-4"),
                    width=6
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(
                            html.B("Logging", className="text-center"),
                            className="bg-light",
                        ),
                        dcc.Graph(
                            id="label-tech-bar-chart-logging",
                            config={"displayModeBar": False},
                            style={"height": 300},
                        ),
                    ], className="mb-4"),
                    width=6
                ),
            ], className="mb-4"),

        ]
    )
