import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

dash.register_page(__name__, path="/overview")

# Layout for the Overview Page
layout = html.Div(
    [
        html.H1("Overview Dashboard", style={"textAlign": "center"}),

        # Month and Year filters
        html.Div(
            [
                html.Label("Select Year:"),
                dcc.Dropdown(
                    id="year-filter",
                    options=[],  # Placeholder; will update dynamically
                    placeholder="Select Year",
                    style={"width": "50%", "marginBottom": "10px"},
                ),
                html.Label("Select Month(s):"),
                dcc.Checklist(
                    id="month-filter",
                    options=[
                        {"label": html.Span("January", style={"padding": "5px"}), "value": 1},
                        {"label": html.Span("February", style={"padding": "5px"}), "value": 2},
                        {"label": html.Span("March", style={"padding": "5px"}), "value": 3},
                        {"label": html.Span("April", style={"padding": "5px"}), "value": 4},
                        {"label": html.Span("May", style={"padding": "5px"}), "value": 5},
                        {"label": html.Span("June", style={"padding": "5px"}), "value": 6},
                        {"label": html.Span("July", style={"padding": "5px"}), "value": 7},
                        {"label": html.Span("August", style={"padding": "5px"}), "value": 8},
                        {"label": html.Span("September", style={"padding": "5px"}), "value": 9},
                        {"label": html.Span("October", style={"padding": "5px"}), "value": 10},
                        {"label": html.Span("November", style={"padding": "5px"}), "value": 11},
                        {"label": html.Span("December", style={"padding": "5px"}), "value": 12},
                    ],
                    inline=True,
                    style={"marginBottom": "20px"},
                ),
            ],
        ),

        # Cards: Total Utilization Rate, Top 5 Specialties, Bottom 5 Specialties
        html.Div(
            [
                # Total Utilization Rate Card
                html.Div(
                    id="total-utilization-card",
                    style={
                        "backgroundColor": "#f9f9f9",
                        "padding": "20px",
                        "borderRadius": "10px",
                        "marginBottom": "20px",
                        "width": "40%",
                        "textAlign": "center",
                        "height": "250px",  # Set fixed height
                        "display": "flex",
                        "flexDirection": "column",
                        "justifyContent": "center",
                        "alignItems": "center",
                    },
                ),

                # Top 5 Specialties Card
                html.Div(
                    id="top-5-card",
                    style={
                        "backgroundColor": "#e6f7e6",  # Green for clarity
                        "padding": "20px",
                        "borderRadius": "10px",
                        "marginBottom": "20px",
                        "width": "25%",
                        "textAlign": "center",
                        "height": "250px",  # Set fixed height
                        "display": "flex",
                        "flexDirection": "column",
                        "justifyContent": "center",
                        "alignItems": "center",
                    },
                ),

                # Bottom 5 Specialties Card
                html.Div(
                    id="bottom-5-card",
                    style={
                        "backgroundColor": "#f7e6e6",  # Red for clarity
                        "padding": "20px",
                        "borderRadius": "10px",
                        "marginBottom": "20px",
                        "width": "25%",
                        "textAlign": "center",
                        "height": "250px",  # Set fixed height
                        "display": "flex",
                        "flexDirection": "column",
                        "justifyContent": "center",
                        "alignItems": "center",
                    },
                ),
            ],
            style={
                "display": "flex",
                "justifyContent": "space-around",  # Ensures equal spacing between cards
                "alignItems": "center",  # Centers the cards vertically
                "marginTop": "20px",
            },
        ),


        # Line graph for utilization rate by month
        html.Div(
            [
                html.H3("Utilization Rate Over Time", style={"textAlign": "center"}),
                dcc.Graph(id="utilization-rate-line"),
            ],
            style={"marginTop": "20px"},
        ),

        # Bar chart for utilization rate by specialty
        html.Div(
            [
                html.H3("Utilization Rate by Specialty", style={"textAlign": "center"}),
                dcc.Graph(id="utilization-rate-bar"),
            ],
            style={"marginTop": "20px"},
        ),

        # Data Table for merged data
        html.Div(
            [
                html.H3("Merged Data Table", style={"textAlign": "center", "marginTop": "20px"}),
                html.Div(id="merged-data-table"),
            ]
        ),
        
        dcc.Store(id="shared-store-processed")
    ],
    style={"padding": "20px"},
)

# Callback to populate year dropdown
@callback(
    Output("year-filter", "options"),
    Input("shared-store-processed", "data"),
)
def update_year_options(processed_data):
    if not processed_data or "total" not in processed_data:
        return []
    df = pd.DataFrame(processed_data["total"])
    years = df["Year"].dropna().unique()
    return [{"label": str(year), "value": year} for year in sorted(years)]


# Callback to update the dashboard based on filters
@callback(
    [
        Output("utilization-rate-line", "figure"),
        Output("utilization-rate-bar", "figure"),
        Output("total-utilization-card", "children"),
        Output("top-5-card", "children"),
        Output("bottom-5-card", "children"),
        Output("merged-data-table", "children"),
    ],
    [
        Input("shared-store-files", "data"),
        Input("shared-store-processed", "data"),
        Input("year-filter", "value"),
        Input("month-filter", "value"),
    ],
)

def update_dashboard(shared_data, processed_data, selected_year, selected_months):
    if not processed_data or "total" not in processed_data:
        return (
            px.line(title="No data available."),
            px.bar(title="No data available."),
            html.Div("No data available.", style={"color": "red"}),
            html.Div("No data available.", style={"color": "red"}),
            html.Div("No data available.", style={"color": "red"}),
            dash_table.DataTable(data=[], columns=[]),
        )

    # Step 1: Convert processed data to DataFrame
    df = pd.DataFrame(processed_data["total"])

    # Step 2: Summarize TotalPatientInRoomHours by Specialty, Month, and Year
    summary_df = df.groupby(["Specialty", "Month", "Year"], as_index=False).agg(
        TotalPatientInRoomHours=("Total Patient In Room Minutes", lambda x: x.sum() / 60)  # Convert minutes to hours
    )

    # Step 3: Ensure records in `dm_df` are unique and rename for alignment
    dm_df = pd.DataFrame(shared_data["dm"])

    # Ensure records in `dm_df` are unique by aggregating duplicate entries
    dm_df = dm_df.groupby(["Services", "Month", "Year"], as_index=False).agg(
        Monday=("Monday", "sum"),
        Tuesday=("Tuesday", "sum"),
        Wednesday=("Wednesday", "sum"),
        Thursday=("Thursday", "sum"),
        Friday=("Friday", "sum"),
        Sum=("Sum", "sum"),  # Aggregate the `Sum` column properly
    )

    # Rename columns for alignment with the rest of the pipeline
    dm_df = dm_df.rename(
        columns={"Services": "Specialty", "Sum": "Total Available Hours"}
    )

    
    # Step 4: Merge summarized data with `dm_df`
    merged_df = pd.merge(
        summary_df,
        dm_df[["Specialty", "Month", "Year", "Total Available Hours"]],
        how="left",
        on=["Specialty", "Month", "Year"],
    )

    # Step 5: Calculate Utilization Rate
    merged_df["UtilizationRate"] = (
        merged_df["TotalPatientInRoomHours"] / merged_df["Total Available Hours"]
    ) * 100

    # Step 6: Filter data based on selected year and months
    if selected_year:
        merged_df = merged_df[merged_df["Year"] == int(selected_year)]
    if selected_months:
        merged_df = merged_df[merged_df["Month"].isin(map(int, selected_months))]

    # Check if data is empty after filtering
    if merged_df.empty:
        return (
            px.line(title="No data available for the selected filters."),
            px.bar(title="No data available for the selected filters."),
            html.Div("No data available.", style={"color": "red"}),
            dash_table.DataTable(data=[], columns=[]),
        )

    # Step 7: Summarize monthly utilization rates (discard specialty)
    monthly_summary = merged_df.groupby(["Month", "Year"], as_index=False).agg(
        TotalPatientInRoomHours=("TotalPatientInRoomHours", "sum"),
        TotalAvailableHours=("Total Available Hours", "sum"),
    )
    monthly_summary["UtilizationRate"] = (
        monthly_summary["TotalPatientInRoomHours"] / monthly_summary["TotalAvailableHours"]
    ) * 100

    # Calculate the mean utilization rate
    mean_utilization_rate = monthly_summary["UtilizationRate"].mean()


    # Create Line Graph
    line_fig = px.line(
        monthly_summary,
        x="Month",
        y="UtilizationRate",
        title="Utilization Rate by Month",
        markers=True,
        labels={"UtilizationRate": "Utilization Rate (%)", "Month": "Month"},
    )

    # Update x-axis and y-axis
    line_fig.update_xaxes(
        tickmode="linear", dtick=1, title="Month",
    )

    # Add Mean Utilization Rate Line
    line_fig.add_hline(
        y=mean_utilization_rate,
        line_dash="dash",
        line_color="red",
        annotation_text="Mean Utilization Rate",
    )

    # Step 8: Create Grouped Bar Chart
    merged_df["Month-Year"] = merged_df["Month"].astype(str) + "-" + merged_df["Year"].astype(str)  # Combine Month-Year

    # Compute mean utilization rate per specialty
    specialty_means = merged_df.groupby('Specialty')['UtilizationRate'].mean().reset_index()

    # Sort specialties by mean utilization rate in descending order
    specialty_means = specialty_means.sort_values('UtilizationRate', ascending=False)
    ordered_specialties = specialty_means['Specialty'].tolist()

    # Reorder 'Specialty' in merged_df according to mean utilization rate
    merged_df['Specialty'] = pd.Categorical(merged_df['Specialty'], categories=ordered_specialties, ordered=True)

    #print(specialty_means, ordered_specialties)
    #print("Specialties in merged_df not in ordered_specialties:")
    #print(set(merged_df['Specialty']) - set(ordered_specialties))
    #print("Data type of Specialty column in merged_df:", merged_df['Specialty'].dtype)

    # Dynamically adjust the height of the bar chart based on the number of specialties
    num_specialties = merged_df["Specialty"].nunique()
    chart_height = max(400, num_specialties * 50)  # Base height is 400px, add 50px per specialty

    bar_fig = px.bar(
        merged_df,
        x="UtilizationRate",
        y="Specialty",
        color="Month-Year",
        barmode="group",  # Grouped bar chart
        title="Utilization Rate by Specialty and Month-Year",
        labels={"UtilizationRate": "Utilization Rate (%)", "Specialty": "Specialty", "Month-Year": "Month-Year"},
        height=chart_height,  # Set dynamic height
        orientation="h",  # Horizontal orientation
        category_orders={"Specialty": ordered_specialties},
    )

    # Update layout for better spacing and readability
    bar_fig.update_layout(
        margin=dict(l=100, r=50, t=50, b=50),  # Add margin for better display
        yaxis=dict(title="Specialty", automargin=True),  # Ensure y-axis labels fit
        xaxis=dict(title="Utilization Rate (%)", tickformat=".0f"),  # Format x-axis
    )

    # Step 9: Create Total Utilization Rate Card
    total_utilization_rate = (
        merged_df["TotalPatientInRoomHours"].sum() / merged_df["Total Available Hours"].sum()
    ) * 100

    # Create the gauge chart
    gauge_fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=total_utilization_rate,
            title={"text": "Total Utilization Rate", "font": {"size": 18}},
            gauge={
                "axis": {
                "range": [0, 100],
                "tickwidth": 0,  # Remove tick marks width to make it minimal
                "tickcolor": "rgba(0,0,0,0)",  # Set tick color to transparent
                },
                "bar": {"color": "teal"},
                "steps": [
                    {"range": [0, 50], "color": "lightcoral"},
                    {"range": [50, 75], "color": "khaki"},
                    {"range": [75, 100], "color": "lightgreen"},
                ],
            "borderwidth": 0,  # Set border width to zero to remove any border lines
            "bordercolor": "rgba(0,0,0,0)",  # Make border color transparent
            },
            number={"suffix": "%"},  # Display as a percentage
        )
    )

    # Add styling to the gauge chart
    gauge_fig.update_layout(
        height=300,  # Make the chart smaller
        width=300,  # Set the width to keep it proportional
        margin=dict(l=10, r=10, t=10, b=10),  # Minimal margin
        paper_bgcolor="rgba(0,0,0,0)",  # Transparent background
        plot_bgcolor="rgba(0,0,0,0)",  # Transparent plot area
    )

    # Replace the total utilization card with the gauge chart
    total_utilization_card = dcc.Graph(
        figure=gauge_fig,
        config={"displayModeBar": False},  # Hide the mode bar for a cleaner look
        style={"height": "100%", "width": "100%"},  # Ensure responsiveness
    )


    # Extract Top 5 and Bottom 5 specialties
    top_5_specialties = specialty_means.nlargest(5, "UtilizationRate")
    bottom_5_specialties = specialty_means.nsmallest(5, "UtilizationRate")

    # Create lists for display
    top_5_list = html.Ul(
        [
            html.Li(
                [
                    html.Span(f"{row['Specialty']}", style={"minWidth": "120px", "textAlign": "left", "display": "inline-block"}),
                    html.Span(f"{row['UtilizationRate']:.2f}%", style={"textAlign": "left", "display": "inline-block"}),
                ],
                style={"padding": "5px 0"}
            )
            for _, row in top_5_specialties.iterrows()
        ],
        style={
            "listStyleType": "none",  # Removes bullet points
            "padding": "0",           # Removes default padding
            "margin": "0",            # Removes default margin
        },
    )

    bottom_5_list = html.Ul(
        [
            html.Li(
                [
                    html.Span(f"{row['Specialty']}", style={"minWidth": "120px", "textAlign": "left", "display": "inline-block"}),
                    html.Span(f"{row['UtilizationRate']:.2f}%", style={"textAlign": "left", "display": "inline-block"}),
                ],
                style={"padding": "5px 0"}
            )
            for _, row in bottom_5_specialties.iterrows()
        ],
        style={
            "listStyleType": "none",  # Removes bullet points
            "padding": "0",           # Removes default padding
            "margin": "0",            # Removes default margin
        },
    )

    # Card for Top 5 Specialties
    top_5_card = html.Div(
        [
            html.H3("Top 5"),
            top_5_list,
        ],
    )

    # Card for Bottom 5 Specialties
    bottom_5_card = html.Div(
        [
            html.H3("Bottom 5"),
            bottom_5_list,
        ],
    )

    # Step 10: Create Merged Data Table
    data_table = dash_table.DataTable(
        data=merged_df.to_dict("records"),
        columns=[
            {"name": col, "id": col}
            for col in ["Specialty", "Month", "Year", "TotalPatientInRoomHours", "Total Available Hours", "UtilizationRate"]
        ],
        page_size=10,
        style_table={"overflowX": "auto"},
    )

    return line_fig, bar_fig, total_utilization_card, top_5_card, bottom_5_card, data_table
