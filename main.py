#!/usr/bin/env python3

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
import logging

from tickers import TickerScraper

if __name__ == '__main__':
    __SHA_USA__ = 'faebc1d6-b91c-41c4-a506-d2c6e6fc96a8'
    __SHA_CANADA__ = 'e6400abd-ea79-47e4-a637-fa0d6f928183'

    get_list_of_stocks_USA = TickerScraper(wait_time=5)
    get_list_of_stocks_USA.main(sha=__SHA_USA__)

    get_list_of_stocks_CANADA = TickerScraper(wait_time=5)
    get_list_of_stocks_CANADA.main(sha=__SHA_CANADA__)



