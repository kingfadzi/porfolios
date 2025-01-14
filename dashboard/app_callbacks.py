from dash import Input, Output
from data.fetch_dropdown_options import fetch_dropdown_options
from data.fetch_contributors_commits_size import fetch_contributors_commits_size
from data.fetch_iac_data import fetch_iac_data
from data.fetch_active_inactive_data import fetch_active_inactive_data
from data.fetch_classification_data import fetch_classification_data
from data.fetch_language_data import fetch_language_data
from data.fetch_heatmap_data import fetch_heatmap_data
from callbacks.viz_contributors_commits_size import viz_contributors_commits_size
from callbacks.viz_iac_chart import viz_iac_chart
from callbacks.viz_active_inactive import viz_active_inactive
from callbacks.viz_classification import viz_classification
from callbacks.viz_main_language import viz_main_language
from data.fetch_cloc_by_language import fetch_cloc_by_language
from callbacks.viz_cloc_by_language import viz_cloc_by_language
from data.fetch_language_contributors_heatmap import fetch_language_contributors_heatmap
from callbacks.viz_language_contributors_heatmap import viz_language_contributors_heatmap


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
        [Input("app-layout", "children")]  # Trigger callback when layout is loaded
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
            Output("active-inactive-bar", "figure"),                # 1. Active vs Inactive Repositories
            Output("classification-pie", "figure"),                 # 2. Repository Classification
            Output("scatter-plot", "figure"),                       # 3. Contributors vs Commits Scatter Plot
            Output("repos-by-language-bar", "figure"),              # 4. Repositories by Main Language
            Output("cloc-bar-chart", "figure"),                     # 5. CLOC Metrics by Language
            Output("iac-bar-chart", "figure"),                      # 6. Repositories by IaC Type
            Output("language-contributors-heatmap", "figure"),      # 7. Programming Languages vs Contributor Buckets Heatmap


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
        # Parse the app_id input
        if app_id_input:
            app_ids = [id.strip() for id in app_id_input.split(",")]
        else:
            app_ids = None

        # Create a dictionary of filters dynamically
        filters = {
            "host_name": selected_hosts,
            "activity_status": selected_statuses,
            "tc_cluster": selected_tc_clusters,
            "tc": selected_tcs,
            "main_language": selected_languages,
            "classification_label": selected_classifications,
            "app_id": app_ids,
        }

        # Fetch data for each visualization
        active_inactive_data = fetch_active_inactive_data(filters)
        contributors_commits_size_data = fetch_contributors_commits_size(filters)
        iac_data = fetch_iac_data(filters)
        classification_data = fetch_classification_data(filters)
        language_data = fetch_language_data(filters)
        heatmap_data = fetch_heatmap_data(filters)
        cloc_data = fetch_cloc_by_language(filters)
        heatmap_data = fetch_language_contributors_heatmap(filters)

    # Generate visualizations
        scatter_fig = viz_contributors_commits_size(contributors_commits_size_data)
        iac_chart_fig = viz_iac_chart(iac_data)
        active_inactive_fig = viz_active_inactive(active_inactive_data)
        classification_fig = viz_classification(classification_data)
        language_chart_fig = viz_main_language(language_data)
        cloc_chart_fig = viz_cloc_by_language(cloc_data)
        heatmap_fig = viz_language_contributors_heatmap(heatmap_data)

        return (
            active_inactive_fig,                # 1
            classification_fig,                 # 2
            scatter_fig,                        # 3
            language_chart_fig,                 # 4
            cloc_chart_fig,                     # 5
            iac_chart_fig,                      # 6
            heatmap_fig,  # 7

        )

