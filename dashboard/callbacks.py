from dash import Input, Output
from callbacks.viz_functions import create_bar_chart, create_pie_chart, create_heatmap, create_language_bar_chart

def register_callbacks(app, df):
    @app.callback(
        [
            Output("active-inactive-bar", "figure"),
            Output("classification-pie", "figure"),
            Output("heatmap-viz", "figure"),
            Output("repos-by-language-bar", "figure"),
        ],
        [
            Input("host-name-filter", "value"),
            Input("language-filter", "value"),
            Input("app-id-filter", "value"),
            Input("classification-filter", "value"),
        ],
    )
    def update_charts(selected_hosts, selected_languages, selected_app_ids, selected_classifications):
        filtered_df = df.copy()
        if selected_hosts:
            filtered_df = filtered_df[filtered_df["host_name"].isin(selected_hosts)]
        if selected_languages:
            filtered_df = filtered_df[filtered_df["main_language"].isin(selected_languages)]
        if selected_app_ids:
            filtered_df = filtered_df[filtered_df["app_id"].isin(selected_app_ids)]
        if selected_classifications:
            filtered_df = filtered_df[filtered_df["classification_label"].isin(selected_classifications)]

        return (
            create_bar_chart(filtered_df),
            create_pie_chart(filtered_df),
            create_heatmap(filtered_df),
            create_language_bar_chart(filtered_df),
        )