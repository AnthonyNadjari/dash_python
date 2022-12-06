from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup as bs
import pandas as pd
import time
import numpy as np
import os
from datetime import datetime
from pandas.tseries.offsets import BDay

# tickers to be used
tickers = ['AAPL', 'MSFT', 'TSLA', 'AMZN', 'NFLX','GOOGL','UNH','NVDA', 'JPM','PFE','NKE','GS','AMD','MS','SBUX','GM','AC','BNP','EN','ACA','BN','ENGI','MC','GLE','SAF', 'BMW', 'SIE']

# Today's date
today=datetime.today().strftime('%Y-%m-%d')

# indicates if a web driver is already active
browser_launched=False

# if needed, we launch the Firefox driver
def launch_browser(ticker):
    """Function that launches the browser

    Action:
        Opens web driver and navigates to historical prices for given ticker
    """
    global browser_launched
    global driver
    if not browser_launched:
        driver = webdriver.Firefox(executable_path=r'./driver/geckodriver')
    url = "https://www.advfn.com/stock-market/"
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    # Enter ticker in search bar
    driver.find_element(By.CSS_SELECTOR, '#headerQuickQuoteSearch').send_keys(ticker)
    time.sleep(1)
    # focus on search bar to have suggestions
    driver.find_element(By.CSS_SELECTOR, '#headerQuickQuoteSearch').click()
    # wait until the first element in the list is clickable
    el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#headerQuickQuoteSearch-menu > table > tbody > tr:nth-child(1)')))
    # the exchange is plugged into the url to retrieve quotes 
    # (we use the suggestion box because we assume user might not know the exchange)
    info = driver.find_element(By.CSS_SELECTOR, 'tr.autosuggest-result').text
    exchange_split = info.split(" ")
    exchange = exchange_split[len(exchange_split)-1]
    if exchange == "EU":
        exchange = "EURONEXT"
    url = "https://www.advfn.com/stock-market/"+ exchange +"/" + ticker + "/historical/more-historical-data"
    driver.get(url)
    browser_launched = True



def retrieve_prices_ADVFN(ticker, dfrom, dto):
    """Function that gets data from ADVFN

    Args:
        dfrom (str date 'yyyy-mm-dd'): Initial date
        dto (str date 'yyyy-mm-dd'): End date

    Returns:
        [DataFrame]: Pandas dataframe with CLOSE / OPEN / HIGH / LOW
    """
    global driver

    launch_browser(ticker)

    # input dates into browser with selenium
    driver.find_element(By.CSS_SELECTOR, '#Date1').clear()
    driver.find_element(By.CSS_SELECTOR, '#Date1').send_keys(dfrom)
    driver.find_element(By.CSS_SELECTOR, '#Date2').clear()
    driver.find_element(By.CSS_SELECTOR, '#Date2').send_keys(dto)
    driver.find_element(By.CSS_SELECTOR, '#submit-btn').click()

    dates = []
    prices = []
    i = 1
    # get prices with beautiful soup
    while True:
        html = driver.page_source
        soup = bs(html, 'lxml')
        elements = soup.find_all('tr', {"class": "result"})
        for element in elements:
            date = element.find_all('td')[0].text
            close = element.find_all('td')[1].text
            open = element.find_all('td')[4].text
            high = element.find_all('td')[5].text
            low = element.find_all('td')[6].text
            dates.append(date)
            prices.append([close, open, high, low])
        if len(elements) < 50:
            break
        try:
            # next page
            driver.find_element(By.CSS_SELECTOR, '#next').click()
        except NoSuchElementException:
            break
        i += 1
        
    np_prices=np.array(prices)
    # create and return dataframe with prices for specific period
    df = pd.DataFrame.from_dict({'Date'  : dates,'Close' : np_prices[:,0],'Open' : np_prices[:,1],'High' : np_prices[:,2],'Low' : np_prices[:,3]})
    return df

def get_CSV(ticker):
    """Function that gets data from CSV files

    Args:
        ticker (str): Ticker symbol

    Returns:
        [DataFrame]: Pandas dataframe with CLOSE / OPEN / HIGH / LOW
    """
    directory = 'HistoPrices'
    for filename in os.listdir(directory):
        # get filenames in directory (ticker and time horizon)
        filename = filename[:len(filename)-4]
        file_split = filename.split('_')
        ticker_file = file_split[0]
        # if we get a match then we extract prices
        if ticker == ticker_file:
            prices_histo = pd.read_csv('HistoPrices/' + filename + '.csv')
            prices_histo.drop(columns = prices_histo.columns[0], axis = 1, inplace= True)
            prices_histo.head()
            prices_histo['Date'] = pd.to_datetime(prices_histo['Date'])
            prices_histo = prices_histo.iloc[::-1]
            return prices_histo
    return []

def date_formatting(start_date, end_date):
    """Function that creates various Date Formats for closest business day

    Args:
        start_date (str): YYYY-mm-dd
        end_date (str): YYYY-mm-dd

    Returns:
        start_date: closest Bday YYYY-mm-dd
        end_date: closest Bday YYYY-mm-dd
        start_date_num: closest Bday date format
        end_date_num: closest Bday date format
        start_date_ADVFN: closest Bday mm/dd/yy
        end_date_ADVFN: closest Bday mm/dd/yy
    """

    # We need to take the next closest Business day if user selects week end
    start_date_num = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date_num = datetime.strptime(end_date, "%Y-%m-%d").date()
    if not(bool(len(pd.bdate_range(start_date_num, start_date)))):
        start_date = datetime.strftime(start_date_num + BDay(1), '%Y-%m-%d')
        start_date_num = (start_date_num + BDay(1)).date() 
    if not(bool(len(pd.bdate_range(end_date_num, start_date)))):
        end_date = datetime.strftime(end_date_num - BDay(1), '%Y-%m-%d')
        end_date_num = (end_date_num - BDay(1)).date() 
    
    # start date in format mm/dd/yy
    start_date_split = start_date.split("-")
    start_date_ADVFN = start_date_split[1] + "/" + start_date_split[2] + "/" + start_date_split[0][2:]
    # end date in format mm/dd/yy
    end_date_split = end_date.split("-")
    end_date_ADVFN = end_date_split[1] + "/" + end_date_split[2] + "/" + end_date_split[0][2:]
    
    return start_date, end_date, start_date_num, end_date_num, start_date_ADVFN, end_date_ADVFN


def get_prices(ticker, start_date, end_date):
    """Function that gets data from CSV files + ADVFN

    Args:
        ticker (str): Ticker symbol
        start_date (str date 'yyyy-mm-dd'): Initial date
        end_date (str date 'yyyy-mm-dd'): End date

    Returns:
        [DataFrame]: Pandas dataframe with CLOSE / OPEN / HIGH / LOW
    """

    global browser_launched
    global driver

    # initialize variables
    prices_histo = get_CSV(ticker)

    # Date formatting
    dates = date_formatting(start_date, end_date)
    start_date = dates[0] # str date format yyyy-mm-dd
    end_date = dates[1] # str date format yyyy-mm-dd
    start_date_num = dates[2] # date format
    end_date_num = dates[3] # date format
    start_date_ADVFN = dates[4] # str date format mm/dd/yy 
    end_date_ADVFN = dates[5] # str date format mm/dd/yy 

    # ----------- NO STORED PRICES -------------
    if len(prices_histo)<2:
        # if there is no prior txt file
        df_to_save = df_to_use = retrieve_prices_ADVFN(ticker, start_date_ADVFN,end_date_ADVFN)
    else:
        # ----------- MORE RECENT DATA NEEDS TO BE ADDED -------------
        if prices_histo.iloc[0,0].date() < end_date_num:

            # if the last time we stored AAPL prices was a month ago, then we will add the prices from this month to the list
            latest_prices = retrieve_prices_ADVFN(ticker, datetime.strftime(prices_histo.iloc[0,0], '%m/%d/%y'), end_date_ADVFN)

            # we join the new prices with the txt prices
            frames = [latest_prices, prices_histo]
            df_to_save = df_to_use = pd.concat(frames)

        # ----------- STORED DATA IS UP TO DATE -------------
        else:
            # if the txt prices are already up to date
            df_to_save = df_to_use = prices_histo
        
        df_to_save['Date'] = pd.to_datetime(df_to_save['Date'])

        # ----------- OLDER DATA NEEDS TO BE ADDED -------------
        if prices_histo.iloc[len(prices_histo)-1,0].date() > start_date_num:
            older_prices = retrieve_prices_ADVFN(ticker, start_date_ADVFN,datetime.strftime(prices_histo.iloc[len(prices_histo)-1,0].date(), '%m/%d/%y'))
            frames = [df_to_save, older_prices]
            df_to_save = df_to_use = pd.concat(frames)

        # ----------- STORED DATA HAS ENOUGH HISTORY-------------
        else:
            # if we need 2Y of prices but have 5Y stored, we will extract only 2Y
            i = len(df_to_save)-1
            start_idx = len(df_to_use)-1
            end_idx = 0
            while i > 0:
                # we search from bottom so it will take latest date the 2
                df_date = datetime.strftime(df_to_save.iloc[i,0], '%Y-%m-%d')
                if df_date == end_date:
                    end_idx = i+1
                    break
                elif df_date == start_date:
                    start_idx = i+1
                i-=1
            df_to_use = df_to_save.iloc[end_idx:start_idx,:]

        

    #Drop duplicates (one date will be overlapping)
    df_to_use['Date'] = pd.to_datetime(df_to_use['Date'])
    df_to_save['Date'] = pd.to_datetime(df_to_save['Date'])
    # reverse order so that we go from oldest to newest date
    df_to_use = df_to_use.iloc[::-1]
    df_to_save = df_to_save.iloc[::-1]
    # drop duplicates
    df_to_use = df_to_use.drop_duplicates(subset=['Date']).reset_index(drop=True)
    df_to_save = df_to_save.drop_duplicates(subset=['Date']).reset_index(drop=True)
        


    # save prices to csv file to be used in the future
    df_to_save.to_csv('HistoPrices/' + ticker + '.csv')

    return df_to_use[['Date', 'Close']]



def get_price_table(tickers, start_date, end_date):
    """Function that gets data from ADVFN

    Args:
        tickers (list): List of Ticker symbols
        start_date (datetime): Initial date
        end_date (datetime): End date

    Returns:
        [DataFrame]: Pandas dataframe of close prices for all tickers
    """
    global browser_launched
    global driver

    price_table = None

    #Loop through tickers
    for idx,ticker in enumerate(tickers):

        # will return close price for ticker
        # will also create individual CSV files with CLOSE/OPEN/HIGH/LOW
        df = get_prices(ticker, start_date, end_date)

        # set Date as index to concatenate tables later on
        df.set_index("Date", inplace=True, drop=True)

        # renaming column by ticker
        df = df.rename({'Close': ticker}, axis=1)
        if idx == 0:
            price_table = df
        else:
            price_table = pd.concat([price_table, df], axis=1, join="inner")

        print(price_table)
    
    # close browser
    if browser_launched:
        driver.close()
        driver.quit()

        
    price_table.to_csv('HistoPrices/all_close.csv')

    return price_table



print(get_price_table(tickers, '2011-12-01', today))
