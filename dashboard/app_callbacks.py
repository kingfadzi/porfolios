from dash import Input, Output
from data.data_loader import (
    fetch_active_inactive_data,
    fetch_classification_data,
    fetch_language_data,
    fetch_heatmap_data,
    fetch_dropdown_options,
)
from callbacks.viz_functions import create_bar_chart, create_pie_chart, create_language_chart, create_heatmap, create_code_massive_pie

def register_dropdown_callbacks(app):
    @app.callback(
        [
            Output("host-name-filter", "options"),
            Output("activity-status-filter", "options"),
            Output("tc-cluster-filter", "options"),
            Output("tc-filter", "options"),
            Output("language-filter", "options"),
            Output("classification-filter", "options"),
        ],
        [Input("app-layout", "children")]
    )
    def populate_dropdown_options(_):
        # Fetch dropdown options dynamically
        options = fetch_dropdown_options()

        return (
            [{"label": name, "value": name} for name in options["host_names"]],
            [{"label": status, "value": status} for status in options["activity_statuses"]],
            [{"label": cluster, "value": cluster} for cluster in options["tc_clusters"]],
            [{"label": tc, "value": tc} for tc in options["tcs"]],
            [{"label": lang, "value": lang} for lang in options["languages"]],
            [{"label": label, "value": label} for label in options["classification_labels"]],
        )

def register_callbacks(app):
    @app.callback(
        [
            Output("active-inactive-bar", "figure"),
            Output("classification-pie", "figure"),
            Output("repos-by-language-bar", "figure"),
            Output("heatmap-viz", "figure"),
            Output("code-massive-pie", "figure"),
        ],
        [
            Input("host-name-filter", "value"),
            Input("activity-status-filter", "value"),
            Input("tc-cluster-filter", "value"),
            Input("tc-filter", "value"),
            Input("language-filter", "value"),
            Input("classification-filter", "value"),
            Input("app-id-filter", "value"),
        ],
    )
    def update_charts(selected_hosts, selected_statuses, selected_tc_clusters, selected_tcs, selected_languages, selected_classifications, app_id_input):
        # Parse app_id input
        if app_id_input:
            app_ids = [id.strip() for id in app_id_input.split(",")]
        else:
            app_ids = None

        # Create a dictionary of filters
        filters = {
            "host_name": selected_hosts,
            "activity_status": selected_statuses,
            "tc_cluster": selected_tc_clusters,
            "tc": selected_tcs,
            "main_language": selected_languages,
            "classification_label": selected_classifications,
            "app_id": app_ids,
        }

        # Generate visualizations
        bar_chart_fig = create_bar_chart(fetch_active_inactive_data(filters))
        pie_chart_fig = create_pie_chart(fetch_classification_data(filters))
        language_chart_fig = create_language_chart(fetch_language_data(filters))
        heatmap_fig = create_heatmap(fetch_heatmap_data(filters))
        code_massive_pie_fig = create_code_massive_pie(fetch_classification_data(filters))  # New chart logic

        return bar_chart_fig, pie_chart_fig, language_chart_fig, heatmap_fig, code_massive_pie_fig
