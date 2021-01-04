# -*- coding: utf-8 -*-
# Author: Nik Burmeister
import time
import pandas as pd
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import sys
from datetime import timedelta
from datetime import datetime
import numpy as np
import re



curr_dir = os.path.dirname(os.path.realpath(__file__))
cd_path = os.path.join(curr_dir, "driver", "chromedriver.exe")
chrome_options = Options()
headless = False

if headless:
    chrome_options.add_argument("--headless")

try:
    driver = webdriver.Chrome(executable_path=cd_path, chrome_options=chrome_options)
except:
    driver = webdriver.Chrome(executable_path=cd_path, chrome_options=chrome_options)

base = ""
gtrends = "https://trends.google.com/trends/explore?q={QUERY}&geo=US"

QUERY_LIST = ["apartments for rent in The Woodlands", "apartments for rent milwaukee"]

for query in QUERY_LIST:
    m_query = query.replace(" ", "%20")
    while 1:
        driver.get(gtrends.format(QUERY=m_query))

    print
    # driver.find_element_by_xpath('//*[@id="input-254"]').send_keys(Keys.ENTER)

print
