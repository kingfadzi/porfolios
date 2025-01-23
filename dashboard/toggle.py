from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px

# Sample data
df = pd.DataFrame({
    "Category": ["A", "B", "C", "D"],
    "Value": [10, 20, 30, 40]
})

# Initialize Dash app
app = Dash(__name__)

# App layout
app.layout = html.Div([
    # Filter dropdown on the left
    html.Div([
        dcc.Dropdown(
            id='filter-dropdown',
            options=[{'label': cat, 'value': cat} for cat in df['Category']],
            value=None,
            placeholder="Select Category"
        )
    ], style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top'}),

    # Toggle switch for switching views
    html.Div([
        html.Label("Toggle View:"),
        dcc.RadioItems(
            id='toggle-view',
            options=[
                {'label': 'Visualization', 'value': 'viz'},
                {'label': 'Table', 'value': 'table'}
            ],
            value='viz',
            inline=True,
            inputStyle={"margin-right": "5px", "margin-left": "10px"}
        ),
        html.Div(id='display-area', style={'margin-top': '20px'})
    ], style={'width': '75%', 'display': 'inline-block', 'padding': '10px'})
])

# Callback to update content based on toggle and filter
@app.callback(
    Output('display-area', 'children'),
    [Input('toggle-view', 'value'),
     Input('filter-dropdown', 'value')]
)
def update_view(toggle_view, selected_category):
    # Filter the data
    filtered_df = df[df['Category'] == selected_category] if selected_category else df

    # Show visualization
    if toggle_view == 'viz':
        fig = px.bar(filtered_df, x='Category', y='Value', title="Visualization")
        return dcc.Graph(figure=fig)
    
    # Show table
    elif toggle_view == 'table':
        return html.Table([
            html.Thead(html.Tr([html.Th(col) for col in filtered_df.columns])),
            html.Tbody([
                html.Tr([html.Td(filtered_df.iloc[i][col]) for col in filtered_df.columns])
                for i in range(len(filtered_df))
            ])
        ])

# Run the server
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)