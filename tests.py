import unittest
from financials import FinancialScraper
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor
from selenium.common.exceptions import TimeoutException
from time import sleep
import pickle
import os
import pandas as pd
import requests
import re
import datetime
import shutil
import glob
import time


class TestTickersScraper(unittest.TestCase):
    pass

class TestFinancials(unittest.TestCase):

    def test_get_tickers_links_if_there_is_input_file(self):
        self.assertTrue(FinancialScraper.get_tickers_links(self))
    
    def test_get_tickers_links_if_there_is_not_input_file(self):
        
        def rename_files(name1, name2):
            os.rename(name1,name2)
            print(f"changed name to {name2}" if f"{name2}" in os.listdir() else f"couldn't change {name1} to {name2}")

        rename_files('tickers.pkl','tickers_.pkl')
        self.assertFalse(FinancialScraper.get_tickers_links(self))
        rename_files('tickers_.pkl','tickers.pkl')
    


if __name__ == '__main__':
    unittest.main()