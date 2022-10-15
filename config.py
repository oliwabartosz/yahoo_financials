"""
Here is a config file with basic options.
You can set global options such as:
sleep_time, Selenium driver, logging parameters.
"""
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

import pickle
import logging

# SELENIUM
options = FirefoxOptions()
# options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Firefox(options=options)
wait = WebDriverWait(driver, 5)

# LOGGING


class Logger:
    """
    Sets the logger.

    Attributes:
    :filename: set a filename in which logs will be saved.
    :area: set an area, which is the name of specific logger.

    :return: function logging.getLogger 
    """

    @staticmethod
    def setup(name: str, file_name: str):
        log_file = file_name
        log_format = "%(asctime)s - %(name)-12s: %(levelname)-8s %(message)s"
        log_filemode = "w"  # w - overwrite, a - append
        log_level = logging.INFO

        logger = logging.getLogger(name)

        # File output line
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(log_format)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console output line
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        log_formatter = logging.Formatter(log_format)
        console_handler.setFormatter(log_formatter)
        logger.addHandler(console_handler)
        logger.propagate = 0

        return logger


# OTHER
sleep_time = 5


def rerun_attempt_save(attempt: int) -> None:
    with open('attempt.pkl', 'wb') as file_to_save:
        pickle.dump(attempt, file_to_save)

# RERUNING COUNTER CONFIGUTATION
def rerun_attempt_load():
    try:
        with open('attempt.pkl', 'rb') as file_to_save:
            attempt = pickle.load(file_to_save)
            return attempt
    except FileNotFoundError:
        rerun_attempt_save(0)
