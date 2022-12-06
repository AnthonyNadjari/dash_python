from dash import html, dcc,dash_table,callback
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Output,Input
from dash_bootstrap_templates import load_figure_template
import numpy as np
import ac_bt_interface
import ac_bt



load_figure_template('cerulean')
stocks_layout = dbc.Container( [
    html.H1(
        className='body',
        children = 'Stock Displayer',
        style={'textAlign': 'center','color':'#2fa4e7','fontSize': 28, 'font-weight':'normal'},
    ),
    dbc.Row([
        dbc.Col([
            html.Br(),
            html.Br(),
            dcc.DatePickerRange(
                start_date_placeholder_text='Start Date',
                end_date_placeholder_text='End Period',
                calendar_orientation='vertical',
                display_format='DD/MM/YYYY',
                id='date_range_stocks',
                clearable=True)
            ],width='auto'),
        ],justify='center'),
    dbc.Row([
        dbc.Col([
            html.Div(
                children=[
                    html.Br(),
                    html.P('Underlyings'),
                    dcc.Dropdown(options=ac_bt_interface.get_companies(),
                                 value='',
                                 id='udls_display',
                                 multi=True)]
            )
        ]),
    ]),
    dbc.Row([
        dbc.Col([
            html.Div(id='pandas-output-container')

            ])
        ])
])

@callback(Output('pandas-output-container', 'children'),
              [Input('udls_display', 'value'),
               Input('date_range_stocks','start_date'),
               Input('date_range_stocks','end_date')])
def display(tickers,start_date,end_date):
    df=pd.DataFrame({})
    if len(tickers)==0:
        return dbc.Table.from_dataframe(df)
    for ticker in tickers:
        df_ticker  = pd.read_csv("HistoPrices/" + str(ticker) + ".csv",index_col=1, sep=",",header=0,skiprows=0)
        df_ticker = df_ticker.drop(df_ticker.columns[0], axis=1)
        df_ticker.columns = np.array(df_ticker.columns)+ " " + str(ticker)
        if len(df.index)==0:
            df = df_ticker
        else:
            df = df.join(df_ticker)
    dates = ac_bt.nearest_neighbors_sorted(np.array([start_date,end_date]),df.index)
    df = df.iloc[dates[0]:dates[1]+1,:]
    return dbc.Table.from_dataframe(df.reset_index())

