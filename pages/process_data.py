import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_ag_grid as dag
import pandas as pd
import io
import base64

dash.register_page(__name__, path="/process_data")

# Layout for the page
layout = html.Div(
    [
        html.H1("Process Data", style={"textAlign": "center"}),

        # Single white box for buttons
        html.Div(
            [
                # Process Data button and description
                html.Div(
                    [
                        html.Button(
                            "Process Data",
                            id="process-data-btn",
                            className="btn btn-primary",
                        ),
                        html.P(
                            "Click the button to map the specialty by primary surgeon name or surgical specialty.",
                            style={"fontSize": "12px", "color": "grey", "marginTop": "10px"},
                        ),
                        html.Div(
                            id="process-status",
                            children="",
                            style={"color": "blue", "marginTop": "10px"},
                        ),
                    ],
                    style={"flex": "1", "textAlign": "center", "padding": "20px"},
                ),

                # Export Processed Data button and description
                html.Div(
                    [
                        html.Button(
                            "Export Processed Data",
                            id="export-data-btn",
                            className="btn btn-secondary",
                        ),
                        dcc.Download(id="download-dataframe-xlsx"),
                        html.P(
                            "Export the mapped dataset for further analysis use or specialty adjustment.",
                            style={"fontSize": "12px", "color": "grey", "marginTop": "10px"},
                        ),
                    ],
                    style={"flex": "1", "textAlign": "center", "padding": "20px"},
                ),

                # Update Processed Data button and description
                html.Div(
                    [
                        dcc.Upload(
                            id="upload-replace-processed-data",
                            children=html.Button(
                                "Update Processed Data", className="btn btn-primary"
                            ),
                        ),
                        html.P(
                            "Upload an Excel file to replace the processed dataset.",
                            style={"fontSize": "12px", "color": "grey", "marginTop": "10px"},
                        ),
                        html.Div(
                            id="upload-status",
                            children="",
                            style={"color": "blue", "marginTop": "10px"},
                        ),
                    ],
                    style={"flex": "1", "textAlign": "center", "padding": "20px"},
                ),
            ],
            style={
                "display": "flex",
                "backgroundColor": "white",
                "borderRadius": "8px",
                "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
                "marginBottom": "20px",
            },
        ),

        # Display the processed data
        html.Div(id="processed-data-display"),

        # Persistent Stores
        dcc.Store(id="shared-store-processed"),
        dcc.Store(id="shared-store-replacement"),
    ],
    style={"padding": "20px"},
)



# Consolidated Callback to handle processing, uploading, and displaying data
@callback(
    [
        Output("processed-data-display", "children"),
        Output("shared-store-processed", "data"),
        Output("process-status", "children"),
        Output("upload-status", "children"),
    ],
    [
        Input("process-data-btn", "n_clicks"),
        Input("upload-replace-processed-data", "contents"),
    ],
    [
        State("upload-replace-processed-data", "filename"),
        State("shared-store-files", "data"),
        State("shared-store-processed", "data"),
    ],
    prevent_initial_call=True,
)
def handle_data_processing_or_update(process_clicks, upload_contents, filename, shared_files, processed_data):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Processing data case
    if triggered_id == "process-data-btn":
        if not shared_files or not all(key in shared_files for key in ["nu", "sg", "dm", "dic"]):
            missing_keys = [key for key in ["nu", "sg", "dm", "dic"] if key not in shared_files]
            return (
                html.Div(
                    f"Missing data: {', '.join(missing_keys)}. Please upload all required datasets first.",
                    style={"color": "red", "fontStyle": "italic"},
                ),
                dash.no_update,
                "Error: Missing required datasets.",
                dash.no_update,
            )

        try:
            # Processing logic
            nu_df = pd.DataFrame(shared_files["nu"])
            sg_df = pd.DataFrame(shared_files["sg"])
            dm_df = pd.DataFrame(shared_files["dm"])
            dic_df = pd.DataFrame(shared_files["dic"])
                
            # Step 1: Filter and separate columns in `dic.df`
            dic_filtered = (
                dic_df.dropna(subset=['Name from Raw Data'])
                .query("`Name from Raw Data` != 'NA' and Selection == 'V'")
                .assign(
                    RawName1=lambda x: x['Name from Raw Data'].str.split('/').str[0],
                    RawName2=lambda x: x['Name from Raw Data'].str.split('/').str[1]
                )
                .loc[:, ['Abbreviation', 'Service', 'RawName1', 'RawName2']]
            )

            # Step 2: Remove rows where 'RawName1' appears more than once
            dic_nondup = (
                dic_filtered.groupby('RawName1')
                .filter(lambda x: len(x) == 1)
                .reset_index(drop=True)
            )
            dic_nondup = dic_nondup.rename(columns={'Abbreviation': 'DicAbb', 'Service': 'DicService'})

            # Step 3: Load and create Specialty Abbreviation for Surgeon List
            sg_df['Surgeon'] = sg_df.apply(
                lambda row: f"{row['Last Name']}, {row['First Name']} {row['MI']}" if pd.notna(row['MI'])
                else f"{row['Last Name']}, {row['First Name']}",
                axis=1
            )

            sg_df2 = sg_df[['Surgeon', 'Department1', 'Division1']]

            # Filter the DataFrame for the specified departments
            departments_to_keep = [
                "DENTISTRY", "MEDICINE", "NEUROSURGERY", "OBSTETRICS AND GYNECOLOGY",
                "OPHTHALMOLOGY", "ORTHOPEDICS", "OTOLARYNGOLOGY", "PEDIATRICS",
                "SURGERY", "UROLOGY"
            ]

            sg_df2 = sg_df2[sg_df2['Department1'].isin(departments_to_keep)]

            def determine_specialty(row):
                department = str(row['Department1']).upper()  # Convert Department1 to uppercase
                division = str(row['Division1']).upper()     # Convert Division1 to uppercase

                if department == "OBSTETRICS AND GYNECOLOGY":
                    if division == "GYNECOLOGY ONCOLOGY":
                        return "GYNONC"
                    elif division == "REPRODUCTIVE ENDOCRINE INFERTILITY":
                        return "GYNREI"
                    elif division == "FEMALE PELVIC MED. AND RECONST. SURG":
                        return "GYNURO"
                    else:
                        return "GYN"
                elif department == "DENTISTRY":
                    if division == "PEDIATRIC DENTISTRY":
                        return "PD-DEN"
                    else:
                        return "DENT-OMFS"
                elif department == "SURGERY":
                    if division == "BURNS":
                        return "BURNS"
                    elif division == "CARDIAC SURGERY":
                        return "CAR"
                    elif division == "COLORECTAL":
                        return "CRS"
                    elif division == "HEPATOBILIARY":
                        return "HBS"
                    elif division == "MINIMALLY INVASIVE SURGERY":
                        return "MIS"
                    elif division == "SURGICAL ONCOLOGY":
                        return "ONC"
                    elif division == "THORACIC":
                        return "THO"
                    elif division == "PLASTICS":
                        return "PLAS"
                    elif division == "ACUTE CARE SURGERY (ACS)":
                        return "ACS"
                    elif division == "VASCULAR":
                        return "VAS"
                    elif division == "PEDIATRICS":
                        return "GS-PED"
                    else:
                        return "UNDEFINED"
                elif department == "PEDIATRICS":
                    return "GS-PED"
                elif department == "UROLOGY":
                    return "URO"
                elif department == "OPHTHALMOLOGY":
                    return "OPH"
                elif department == "OTOLARYNGOLOGY":
                    return "OTO"
                elif department == "NEUROSURGERY":
                    return "NEU"
                elif department == "ORTHOPEDICS":
                    if division == "HAND SERVICES":
                        return "ORT-HAND"
                    elif division == "PODIATRY":
                        return "ORT-POD"
                    elif division == "SPORTS MEDICINE":
                        return "ORT-SPT"
                    else:
                        return "ORT"
                else:
                    return "UNDEFINED"

            # Apply the function to assign Specialty
            sg_df2['DivAbb'] = sg_df2.apply(determine_specialty, axis=1)

            # Step 4: Merge DataFrames
            merge_df = (
                nu_df
                .merge(sg_df2, how='left', left_on='Primary Surgeon', right_on='Surgeon')
                .merge(dic_nondup[["DicAbb", "DicService", "RawName1"]], how='left', left_on='Surgical Specialty', right_on='RawName1')  # Merge with dic2 on 'Name1'
                .merge(dic_nondup[["DicAbb", "DicService", "RawName2"]], how='left', left_on='Surgical Specialty', right_on='RawName2')  # Merge with dic2 on 'Name2'
            )

            # Step 5: Create 'Specialty' column based on conditions
            merge_df['Specialty'] = merge_df.apply(
                lambda row: row['DivAbb'] if pd.notna(row['Division1']) else
                            row['DicAbb_x'] if pd.notna(row['DicService_x']) else
                            row['DicAbb_y'] if pd.notna(row['DicService_y']) else "",
                axis=1
            )

            # Step 6: Update 'Specialty' if conditions are met
            robot_specialties = {"ACS", "CRS", "GYN", "GYNONC", "HBS", "MIS", "URO", "THO"}

            # Step 7: Update 'Specialty' based on conditions
                # If procedure contains "robot" then add "ROT-" before specialty
                # If Specialty belongs to plastics & procedures contains "burn" then classified as BURNS
            merge_df['Specialty'] = merge_df.apply(
                lambda row: (
                    f"ROT-{row['Specialty']}" if pd.notna(row['Primary Procedure'])
                    and 'robot' in row['Primary Procedure'].lower()
                    and row['Specialty'] in robot_specialties
                    else "BURNS" if pd.notna(row['Primary Procedure'])
                    and 'burn' in row['Primary Procedure'].lower()
                    and row['Specialty'] == "PLAS"
                    else row['Specialty']
                ),
                axis=1
            )

            # Replace empty string ("") in 'Specialty' with 'UNSPECIFIED' in uppercase
            merge_df['Specialty'] = merge_df['Specialty'].apply(lambda x: x.upper() if x.strip() != "" else "UNDEFINED")

            merge_df = merge_df.drop(columns=['DicAbb_x', 'DicService_x', 'RawName1', 'DicAbb_y', 'DicService_y', 'RawName2'])

            # Ensure records in `dm_df` are unique
            dm_df = dm_df.groupby(["Services", "Month", "Year"], as_index=False).agg(
                Monday=("Monday", "sum"),
                Tuesday=("Tuesday", "sum"),
                Wednesday=("Wednesday", "sum"),
                Thursday=("Thursday", "sum"),
                Friday=("Friday", "sum"),
                Sum=("Sum", "sum"),  # Ensure the `Sum` column is also aggregated properly
            )

            # Step 7: Transform `dm_df` to long format
            dm_df_long = pd.melt(
                dm_df,
                id_vars=["Services", "Month", "Year"],
                value_vars=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                var_name="Weekday",
                value_name="Total Hours"
            ).dropna(subset=['Total Hours'])

            dm_df_long['Weekday'] = pd.Categorical(
                dm_df_long['Weekday'],
                categories=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                ordered=True
            )
            dm_df_long = dm_df_long.sort_values(by=['Services', 'Year', 'Month', 'Weekday']).reset_index(drop=True)

            # Step 8: Finalize and merge data
            # Define the date format
            date_format = "%m/%d/%y %H:%M"  # Matches format like "08/01/24 07:28"

            # Convert 'Patient In Room Date/Time' to datetime using the specified format
            merge_df['Patient In Room Date/Time'] = pd.to_datetime(
                merge_df['Patient In Room Date/Time'],
                format=date_format,
                errors='coerce'  # Coerce invalid formats to NaT
            )

            # Extract the date part and assign it to 'Case Start Date'
            merge_df['Case Start Date'] = merge_df['Patient In Room Date/Time'].dt.date

            # (Optional) Convert 'Case Start Date' back to datetime if needed
            merge_df['Case Start Date'] = pd.to_datetime(merge_df['Case Start Date'])


            merge_df['Month'] = merge_df['Case Start Date'].dt.month
            merge_df['Year'] = merge_df['Case Start Date'].dt.year

            total_df = pd.merge(
                merge_df,
                dm_df_long,
                how='left',
                left_on=['Specialty', 'Month', 'Year', 'Case Start Day'],
                right_on=['Services', 'Month', 'Year', 'Weekday']
            ).drop(columns=['Services', 'Weekday'])

            total_df['TotalPtHours'] = (total_df['Total Patient In Room Minutes'] / 60).round(6)

            # Define AgGrid columns dynamically
            columnDefs = [{"headerName": col, "field": col} for col in total_df.columns]

            # Prepare the data for rendering
            display_table = html.Div(
                [
                    html.P(
                        f"Displaying {len(total_df)} records and {len(total_df.columns)} columns.",
                        style={"marginBottom": "10px", "fontWeight": "bold", "fontSize": "16px"},
                    ),
                    dag.AgGrid(
                        id="processed-data-table",
                        rowData=total_df.to_dict("records"),
                        columnDefs=columnDefs,
                        columnSize=None,
                        defaultColDef={"sortable": True, "filter": True, "resizable": True},
                        dashGridOptions={
                            "domLayout": "autoHeight",
                            "pagination": True,
                            "paginationPageSize": 20,
                        },
                    ),
                ],
                style={
                    "backgroundColor": "white",
                    "padding": "20px",
                    "borderRadius": "8px",
                    "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
                    "minHeight": "800px",
                    "width": "100%",
                    "margin": "0 auto",
                },
            )

            # Store processed data in shared-store-processed
            processed_data = {
                "total": total_df.to_dict("records"),
                "dm": dm_df.to_dict("records"),
                "nu": nu_df.to_dict("records"),
                "dic": dic_df.to_dict("records"),
            }

            return display_table, processed_data, "Processing complete!", dash.no_update

        except Exception as e:
            return (
                html.Div(f"Error: {str(e)}", style={"color": "red"}),
                dash.no_update,
                "Error: Processing failed.",
                dash.no_update,
            )

    # Uploading new dataset case
    elif triggered_id == "upload-replace-processed-data":
        if not upload_contents:
            return (
                html.Div("No file uploaded.", style={"color": "red"}),
                dash.no_update,
                "Error: No file uploaded.",
                dash.no_update,
            )

        try:
            # Decode and process the uploaded file
            content_type, content_string = upload_contents.split(",")
            decoded = base64.b64decode(content_string)
            replacement_data = pd.read_excel(io.BytesIO(decoded))

            # Define column definitions for AgGrid
            columnDefs = [{"headerName": col, "field": col} for col in replacement_data.columns]

            # Prepare the data for rendering
            display_table = html.Div(
                [
                    html.P(
                        f"Displaying {len(replacement_data)} records and {len(replacement_data.columns)} columns.",
                        style={"marginBottom": "10px", "fontWeight": "bold", "fontSize": "16px"},
                    ),
                    dag.AgGrid(
                        id="processed-data-table",
                        rowData=replacement_data.to_dict("records"),
                        columnDefs=columnDefs,
                        columnSize=None,
                        defaultColDef={"sortable": True, "filter": True, "resizable": True},
                        dashGridOptions={
                            "domLayout": "autoHeight",
                            "pagination": True,
                            "paginationPageSize": 20,
                        },
                    ),
                ],
                style={
                    "backgroundColor": "white",
                    "padding": "20px",
                    "borderRadius": "8px",
                    "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
                    "minHeight": "800px",
                    "width": "100%",
                    "margin": "0 auto",
                },
            )

            # Store replacement data in shared-store-processed
            processed_data = {
                "total": replacement_data.to_dict("records"),
            }
        
            # Update upload status message
            upload_status_message = f"File '{filename}' uploaded and processed successfully."

            return display_table, processed_data, dash.no_update, upload_status_message

        except Exception as e:
            return (
                html.Div(f"Error: {str(e)}", style={"color": "red"}),
                dash.no_update,
                f"Error processing file: {str(e)}",
                dash.no_update,
            )

    return (
        html.Div("No action performed.", style={"color": "red"}),
        dash.no_update,
        "No action performed.",
        dash.no_update,
    )


# Callback to export processed data as an Excel file
@callback(
    Output("download-dataframe-xlsx", "data"),
    Input("export-data-btn", "n_clicks"),
    State("shared-store-processed", "data"),
    prevent_initial_call=True,
)
def export_data(n_clicks, shared_data):
    if not shared_data or "total" not in shared_data:
        return None  # No data to export

    # Convert the processed data to a DataFrame
    total_df = pd.DataFrame(shared_data["total"])

    # Export the DataFrame as an Excel file
    return dcc.send_data_frame(total_df.to_excel, "processed_data.xlsx", index=False)
