import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import plotly.express as px

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1BsKymbniKnSCFJAkYbflLoAjd4GzjSRC17NU-hhkFlo/edit#gid=0"
JSON_KEYFILE_PATH = R"C:\Users\oonuk\OneDrive\デスクトップ\streamlit\lms-dx-1febf55abbf8.json"

def get_data_from_gsheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE_PATH, scope)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_url(SPREADSHEET_URL)
    worksheet = sh.worksheet("sheet2")
    data = worksheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
    df = df.rename(columns={'readerNo.': 'readerNo', 'CardID': 'CardID', 'Process': 'Process', 'start': 'start', 'end': 'end', 'diff(second)': 'diff'})
    return df

def process_data(df):
    df['start'] = pd.to_datetime(df['start'])
    df['end'] = pd.to_datetime(df['end'])
    df['Process_padded'] = '\n' + df['Process'] + '\n'
    df['diff'] = pd.to_timedelta(df['diff']).dt.total_seconds().astype(int)
    return df

def plot_gantt_chart(data, selected_date):
    fig = px.timeline(data, x_start='start', x_end='end', y='Process_padded', color='Process')
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(xaxis_range=[datetime.combine(selected_date, datetime.min.time()) + timedelta(hours=9),
                                datetime.combine(selected_date, datetime.min.time()) + timedelta(hours=18)])
    fig.update_traces(marker=dict(line=dict(width=0))) 
    st.plotly_chart(fig)

def get_date_range(df):
    min_date = df['start'].dt.date.min()
    max_date = df['end'].dt.date.max()
    return min_date, max_date

def get_selected_card_ids(df, selected_date):
    selected_card_ids = df.loc[df['start'].dt.date == selected_date, 'CardID'].unique()
    return selected_card_ids

def get_selected_data(df, selected_date, selected_card_id):
    selected_data = df[(df['start'].dt.date == selected_date) & (df['CardID'] == selected_card_id)]
    return selected_data

def calc_process_times(selected_data):
    process_times = selected_data.groupby('Process')['diff'].sum().reset_index()
    process_times['diff'] = process_times['diff'].apply(lambda x: str(timedelta(seconds=x)))
    return process_times

def calc_process_workid_times(selected_data):
    process_workid_times = selected_data.groupby(['Process', 'WorkID'])['diff'].sum().reset_index()
    process_workid_times['diff'] = process_workid_times['diff'].apply(lambda x: str(timedelta(seconds=x)))
    return process_workid_times

def display_tables(process_times, process_workid_times):
    col1, col2 = st.columns(2)
    with col1:
        st.write("Total time per Process:")
        st.dataframe(process_times)
    with col2:
        st.write("Total time per WorkID, grouped by Process:")
        st.dataframe(process_workid_times)

def main():
    st.title("Time on Task")
    df = get_data_from_gsheet()
    df = process_data(df)
    min_date, max_date = get_date_range(df)
    selected_date = st.date_input("Select Date", min_value=min_date, max_value=max_date, value=min_date)
    selected_card_ids = get_selected_card_ids(df, selected_date)
    selected_card_id = st.selectbox("Select Card ID", options=selected_card_ids)
    selected_data = get_selected_data(df, selected_date, selected_card_id)

    if selected_data.empty:
        st.write("No data available for the selected date and Card ID.")
    else:
        plot_gantt_chart(selected_data, selected_date)
        process_times = calc_process_times(selected_data)
        process_workid_times = calc_process_workid_times(selected_data)
        display_tables(process_times, process_workid_times)

if __name__ == "__main__":
    main()

