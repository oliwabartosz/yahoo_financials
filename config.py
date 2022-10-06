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

import logging

# SELENIUM
options = FirefoxOptions()
options.add_argument("--headless")
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
        logging.basicConfig(filename=file_name, format=log_format,
                            filemode=log_filemode, level=log_level, force=True)
        logger = logging.getLogger(name)

        # Console output line
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        log_formatter = logging.Formatter(log_format)
        console_handler.setFormatter(log_formatter)
        logger.addHandler(console_handler)
        logger.propagate = 0
        # logger.handlers = console_handler

        return logger


def set_logger(filename: str, area: str) -> "func":
    """
    Sets the logger.

    Attributes:
    :filename: set a filename in which logs will be saved.
    :area: set an area, which is the name of specific logger.

    :return: function logging.getLogger 
    """
    # logging.FileHandler(filename)

    logger = logging.getLogger(area)

    level = logging.INFO
    logging.basicConfig(filename=filename, filemode='w',
                        format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=level)

    # CONSOLE HANDLER
    console = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)
    #logger.propagate = 0

    return logger


# OTHER
sleep_time = 5
