import dash
from dash import dcc, html, Input, Output, callback, dash_table
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

dash.register_page(__name__, path="/specialty")

# Layout for the Specialty Page
layout = html.Div(
    [
        html.H1("Specialty Dashboard", style={"textAlign": "center"}),

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

        # Specialty filter dropdown
        html.Div(
            [
                html.Label("Select Specialty:"),
                dcc.Dropdown(
                    id="specialty-filter",
                    options=[],  # Placeholder; options will be dynamically updated
                    placeholder="Select Specialty",
                    style={"width": "50%", "marginBottom": "20px"},
                ),
            ]
        ),

        # First bar chart for Utilization Rate
        html.Div(
            [
                html.H3("Utilization Rate by Weekday", style={"textAlign": "center"}),
                dcc.Graph(id="specialty-utilization-bar"),
            ],
            style={"width": "50%", "display": "inline-block"},
        ),

        # Bidirectional bar chart
        html.Div(
            [
                html.H3("Total Patient Hours vs. Available Hours by Weekday", style={"textAlign": "center"}),
                dcc.Graph(id="bidirectional-bar-chart"),
            ],
            style={"width": "50%", "display": "inline-block"},
        ),

        # Box plot
        html.Div(
            [
                html.H3("Distribution of Patient In Room Hours", style={"textAlign": "center"}),
                dcc.Graph(id="patient-hours-box-plot"),
            ],
            style={"marginTop": "20px"},
        ),

        # Table for Primary Surgeon details
        html.Div(
            [
                html.H3("Primary Surgeon Stats", style={"textAlign": "center"}),
                dash_table.DataTable(
                    id="surgeon-table",
                    columns=[
                        {"name": "Primary Surgeon", "id": "Primary Surgeon"},
                        {"name": "Total Cases", "id": "Total Cases"},
                        {"name": "Mean Patient Time (Minutes)", "id": "Mean Patient Time"},
                    ],
                    style_table={"overflowX": "auto", "margin": "0 auto"},
                    style_cell={"textAlign": "center", "padding": "10px"},
                    style_header={
                        "backgroundColor": "rgb(230, 230, 230)",
                        "fontWeight": "bold",
                    },
                ),
            ],
            style={"width": "80%", "display": "inline-block", "verticalAlign": "top"},
        ),

        # Persistent store for processed data
        dcc.Store(id="shared-store-processed"),
    ],
    style={"padding": "20px"},
)


# Callback to populate the Specialty dropdown
@callback(
    Output("specialty-filter", "options"),
    
    Input("shared-store-processed", "data"),
)
def update_specialty_options(processed_data):
    if not processed_data or "total" not in processed_data:
        return []
    df = pd.DataFrame(processed_data["total"])
    specialties = df["Specialty"].dropna().unique()
    return [{"label": specialty, "value": specialty} for specialty in sorted(specialties)]
    


@callback(
    [
        Output("specialty-utilization-bar", "figure"),
        Output("bidirectional-bar-chart", "figure"),
        Output("patient-hours-box-plot", "figure"),
        Output("surgeon-table", "data"),
    ],
    [
        Input("shared-store-files", "data"),
        Input("shared-store-processed", "data"),
        Input("specialty-filter", "value"),
    ],
)

def update_charts(shared_data, processed_data, selected_specialty):
    if not processed_data or "total" not in processed_data:
        return (
            px.bar(title="No data available."),
            px.bar(title="No data available."),
        )

    # Convert processed data to DataFrame
    df = pd.DataFrame(processed_data["total"])
    dm_df = pd.DataFrame(shared_data["dm"])

    # Process `dm_df` to ensure records are unique and transform to long format
    dm_df = dm_df.groupby(["Services", "Month", "Year"], as_index=False).agg(
        Monday=("Monday", "sum"),
        Tuesday=("Tuesday", "sum"),
        Wednesday=("Wednesday", "sum"),
        Thursday=("Thursday", "sum"),
        Friday=("Friday", "sum"),
        Sum=("Sum", "sum"),
    )

    dm_df_long = pd.melt(
        dm_df,
        id_vars=["Services", "Month", "Year"],
        value_vars=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        var_name="Weekday",
        value_name="Total Hours",
    ).dropna(subset=["Total Hours"])

    dm_df_long["Weekday"] = pd.Categorical(
        dm_df_long["Weekday"],
        categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        ordered=True,
    )

    dm_df_long = dm_df_long.sort_values(by=["Services", "Year", "Month", "Weekday"]).reset_index(drop=True)

    # Calculate Utilization Rate for the total dataset
    # Use 0 if no hours are available
    df["Total Hours"] = df["Total Hours"].fillna(0)  
    df["UtilizationRate"] = (df["Total Patient In Room Minutes"] / 60) / df["Total Hours"] * 100
    df["Weekday"] = pd.Categorical(
        df["Case Start Day"],
        categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        ordered=True,
    )
    # Add metrics annotations for each box (mean/median values)
    df["Month-Year"] = df["Month"].astype(str) + "-" + df["Year"].astype(str)  # Combine Month-Year

    # Perform right join between `df` and `dm_df_long`
    bar_df = pd.merge(
        dm_df_long,
        df,
        how="left",
        left_on=["Services", "Weekday", "Month", "Year"],
        right_on=["Specialty", "Weekday", "Month", "Year"],
    )

    # Filter by Specialty if selected
    if selected_specialty:
        df = df[df["Specialty"] == selected_specialty]
        dm_df_long = dm_df_long[dm_df_long["Services"] == selected_specialty]
        bar_df = bar_df[bar_df["Services"] == selected_specialty]

    # Group left data by Weekday and Specialty
    left_df = df.groupby(["Specialty", "Month", "Year", "Case Start Day"], as_index=False).agg(
        TotalPatientInRoomHours=("Total Patient In Room Minutes", lambda x: x.sum() / 60)
    )

    # Group Specialty data (dm_df_long) by Weekday and Services
    right_df = dm_df_long.groupby(["Services", "Month", "Year", "Weekday"], as_index=False).agg(
        TotalAvailableHours=("Total Hours", "sum")
    )

    # Ensure Weekday is sorted correctly
    left_df["Weekday"] = pd.Categorical(
        left_df["Case Start Day"], categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], ordered=True
    )
    right_df["Weekday"] = pd.Categorical(
        right_df["Weekday"], categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], ordered=True
    )

    # Merge data for alignment
    merged_data = pd.merge(
        right_df,
        left_df,
        left_on=["Services", "Month", "Year", "Weekday"],
        right_on=["Specialty", "Month", "Year", "Case Start Day"],
        how="left"
    ).fillna(0)

    # Rename columns for clarity
    merged_data = merged_data.rename(
        columns={
            "TotalPatientInRoomHours": "Left_TotalPatientInRoomHours",
            "TotalAvailableHours": "Right_TotalAvailableHours",
        }
    )

    # Create the bidirectional bar chart
    bidirectional_fig = go.Figure()

    # Add left bar
    bidirectional_fig.add_trace(
        go.Bar(
            y=merged_data["Weekday_x"],
            x=-merged_data["Left_TotalPatientInRoomHours"],
            name="Total Patient In Room Hours",
            orientation="h",
            marker=dict(color="lightblue"),
        )
    )

    # Add right bar
    bidirectional_fig.add_trace(
        go.Bar(
            y=merged_data["Weekday_x"],
            x=merged_data["Right_TotalAvailableHours"],  # Negative values for right-side alignment
            name="Total Available Hours",
            orientation="h",
            marker=dict(color="lightgreen"),
        )
    )

    # Update layout for bidirectional bar chart
    bidirectional_fig.update_layout(
        title="Bidirectional Bar Chart: Total Patient In Room Hours vs. Total Available Hours",
        yaxis=dict(
            title="Weekday",
            categoryorder="array",  # Order by a custom array
            categoryarray=["Friday" , "Thursday", "Wednesday", "Tuesday", "Monday"],  # Explicit ordering
        ),
        xaxis=dict(
            title="Hours",
            tickmode="array",
            tickvals=[
                -max(merged_data["Left_TotalPatientInRoomHours"]),
                0,
                max(merged_data["Right_TotalAvailableHours"]),
            ],
            ticktext=[
                f"{max(merged_data['Left_TotalPatientInRoomHours']):,.0f} (Patient)",
                "0",
                f"{max(merged_data['Right_TotalAvailableHours']):,.0f} (Available)",
            ],
        ),
        barmode="relative",
        bargap=0.1,
        legend=dict(title="Metric"),
    )

    # Create the first bar chart for Utilization Rate
    hover_data = {
        "Weekday": True,
        "TotalPtHours": ":.2f",
        "Total Hours_x": ":.2f",
        "UtilizationRate": ":.2f",
    }
    
    bar_df = bar_df.sort_values("Weekday")

    utilization_bar_fig = px.bar(
        bar_df,
        x="Weekday",
        y="UtilizationRate",
        color="Weekday",
        hover_data=hover_data,
        title=f"Utilization Rate by Weekday for {selected_specialty if selected_specialty else 'All Specialties'}",
        labels={"UtilizationRate": "Utilization Rate (%)"},
    )

    utilization_bar_fig.update_layout(
        xaxis=dict(
        categoryorder="array",
        categoryarray=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        ),
        xaxis_title="Weekday",
        yaxis_title="Utilization Rate (%)",
        legend_title="Day",
        showlegend=False,
    )

    # Create the box plot
    box_plot = px.box(
        df,
        x="Specialty",
        y="Total Patient In Room Minutes",
        points="all",
        color="Month-Year",
        title=f"Distribution of Patient In Room Hours for {selected_specialty if selected_specialty else 'All Specialties'}",
        labels={"Total Patient In Room Minutes": "Patient In Room Hours (Minutes)"},
    )
    
    for specialty in df["Specialty"].unique():
        specialty_data = df[df["Specialty"] == specialty]["Total Patient In Room Minutes"]
        median = specialty_data.median()
        mean = specialty_data.mean()

        # Add annotation for median
        box_plot.add_trace(
            go.Scatter(
                x=[specialty], 
                y=[median],
                mode="markers+text",
                text=[f"Median: {median:.2f}"],
                textposition="top center",
                marker=dict(color="black", size=10, symbol="diamond"),
                showlegend=False,
            )
        )

        # Add annotation for mean
        box_plot.add_trace(
            go.Scatter(
                x=[specialty], 
                y=[mean],
                mode="markers+text",
                text=[f"Mean: {mean:.2f}"],
                textposition="bottom center",
                marker=dict(color="blue", size=8, symbol="circle"),
                showlegend=False,
            )
        )

    box_plot.update_layout(
        yaxis_title="Patient In Room Minutes",
        xaxis_title="Specialty",
        yaxis=dict(tickformat=".0f"),
    )

    # Create the table for Primary Surgeons
    surgeon_stats = (
        df.groupby("Primary Surgeon", as_index=False)
        .agg(
            Total_Cases=("Case Start Day", "count"),
            Mean_Patient_Time=("Total Patient In Room Minutes", "mean"),
        )
        .rename(columns={"Total_Cases": "Total Cases", "Mean_Patient_Time": "Mean Patient Time"})
    )
    surgeon_table_data = surgeon_stats.to_dict("records")

    return utilization_bar_fig, bidirectional_fig, box_plot, surgeon_table_data