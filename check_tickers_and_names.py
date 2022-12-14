"""
This program will take tickers links generated by prices_and_tickers_links.py
and then it will grab the names of companies of that tickers.

Then it will take tickers and grab their names from gurufocous.
The output will help to check if tickers from yahoo are equal to gurufocus.
"""

import pickle
import os
import re
from datetime import date
import config
import re


logger_1 = config.Logger.setup(
    name='tickers_and_names', file_name='tickers_and_names.log')

# Open a file with tickers links

with open('tickers.pkl', "rb") as tickers_links_file:
    tickers_links_list = pickle.load(tickers_links_file)


class YahooNameTaker:
    """
    It download the names of companies that are behind tickers links
    from yahoo
    """

    def __init__(self):
        self.yahoo_tickers_names = {}

    def go_to_link(self, ticker_link):
        config.driver.get(ticker_link)
        logger_1.info(f'Going to {ticker_link}.')

    def accept_cookie(self) -> bool:
        """
        Checks if there is a popup with cookies. If so, it clicks accept button.
        """
        cookie_button_accept_xpath = "//button[@class='btn primary']"
        try:
            config.wait.until(config.EC.visibility_of_element_located(
                (config.By.XPATH, cookie_button_accept_xpath)))
            config.driver.find_element(
                "xpath", cookie_button_accept_xpath).click()
            logger_1.info("Cookies accepted.")
            return True
        except config.TimeoutException as e:
            logger_1.info("Cookies confirmation not needed.")
            return False

    def split_ticker_or_name_by_regex(self, company_name_and_ticker: str, ticker: bool):
        """
        If ticker is set to True, it will return a ticker, otherwise takes company's name
        """
        regex = r'\(.+\)'
        regex = re.findall(regex, company_name_and_ticker)[0]

        company_name = company_name_and_ticker.rstrip(regex)
        company_ticker = company_name_and_ticker.strip(
            company_name).strip('()')

        if ticker:
            logger_1.info(f'Got ticker -- {company_ticker} -- from regex')
            return company_ticker
        else:
            logger_1.info(f'Got name -- {company_name} -- from regex')
            return company_name

    def get_company_name_and_ticker(self) -> str:
        xpath_name_and_ticker = "//h1[@class='D(ib) Fz(18px)']"
        company_name_with_ticker = config.driver.find_element(
            "xpath", xpath_name_and_ticker).text
        logger_1.info(f'Got name: {company_name_with_ticker}:')
        return company_name_with_ticker

    def save_data(self):
        pass


get_companies_names_and_tickers_from_yahoo = YahooNameTaker()
for link in tickers_links_list[:1]:
    print(link)
    get_companies_names_and_tickers_from_yahoo.go_to_link(link)
    get_companies_names_and_tickers_from_yahoo.accept_cookie()
    company_and_ticker_name = get_companies_names_and_tickers_from_yahoo.get_company_name_and_ticker()
    company_name = get_companies_names_and_tickers_from_yahoo.split_ticker_or_name_by_regex(
        company_and_ticker_name, False)
    print(company_name)
    ticker_name = get_companies_names_and_tickers_from_yahoo.split_ticker_or_name_by_regex(
        company_and_ticker_name, True)
    print(ticker_name)
