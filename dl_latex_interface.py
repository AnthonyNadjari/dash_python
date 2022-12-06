from dash import html, dcc,dash_table,callback
import dash_bootstrap_components as dbc
from dash import Output,Input,State,callback_context
from dash_bootstrap_templates import load_figure_template
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.by import By


def download():
    browser = webdriver.Chrome(ChromeDriverManager().install())
    browser.get(
        "https://github.com/AnthonyNadjari/zez/blob/main/20110921___Letter_to_ESMA_re_discussion_paper_on_ETF_guidelines.pdf")

    button = browser.find_element(By.CSS_SELECTOR,"#raw-url")
    button.click()
    time.sleep(3)
    browser.close()



load_figure_template('cerulean')
layout_latex = dbc.Container([

        dbc.Col([dbc.Button('Download',
                           id='dl-button',
                           n_clicks=0,
                           color="primary"),
        ]),

        dbc.Row([
            dbc.Col([dcc.Loading(id='loading-1',
                    type="default",
                    children = dbc.Col(id="PRINTOUTPUT"))
                     ]),
            ])

    ])



@callback(Output('PRINTOUTPUT', 'children'),
              [Input('dl-button', 'n_clicks')])

def download_file(n_clicks):
    change_id = [p['prop_id'].split('.')[0] for p in callback_context.triggered]

    if 'dl-button' in change_id:
        download()
#        test_latex.download(path)

    return None