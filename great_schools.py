# -*- coding: utf-8 -*-
# Author: Nik Burmeister
import time
import pandas as pd
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys
from datetime import timedelta
from datetime import datetime
import numpy as np
import re
from selenium.webdriver.common.keys import Keys



import sys


headless = False

curr_dir = os.path.dirname(os.path.realpath(__file__))
cd_path = os.path.join(curr_dir, "driver", "chromedriver.exe")
chrome_options = Options()

#chrome_options.add_argument("user-data-dir=C:\\Users\\nburmeister\\AppData\\Local\\Google\\Chrome\\User Data")

if headless:
    chrome_options.add_argument("--headless")

try:
    driver = webdriver.Chrome(executable_path=cd_path, chrome_options=chrome_options)
except:
    driver = webdriver.Chrome(executable_path=cd_path, chrome_options=chrome_options)

base = "https://www.greatschools.org/"
driver.get(base)
curr_dir = os.path.join(os.path.dirname(__file__))
# public_schools = os.path.join(curr_dir, "data", "schools", "Public_Schools.xlsx")
# #pub_schools_df = pd.read_excel(public_schools)
private_schools = os.path.join("data", "schools", "Private_Schools.xlsx")
pri_schools_df = pd.read_excel(private_schools)


private_school_addresses = pri_schools_df['ADDRESS'].astype(str) + ", " + pri_schools_df['CITY'] + ", " + \
                           pri_schools_df['STATE'] + " " + pri_schools_df['ZIP'].astype(str)


import random
pri_school_addr_list = private_school_addresses.values.tolist()
for school in pri_school_addr_list:
    driver.get(base)
    sleep_time = random.randint(0, 1)
    driver.find_element_by_xpath('//*[@id="home-page"]/div[1]/div/section/div[1]/div[1]/div/div/div/div[1]/form/input').send_keys(school)
    time.sleep(1)
    driver.find_element_by_xpath('//*[@id="home-page"]/div[1]/div/section/div[1]/div[1]/div/div/div/div[1]/form/input').send_keys(Keys.ENTER)

    time.sleep(5)
    page_divs = driver.find_elements_by_css_selector("div")
    for i, div in enumerate(page_divs):
        print(div.text)
        if div.text == 'Assigned school':
            print


    # Search-react-component-0af84deb-7d1f-46d3-b1df-3141e3efca30 > div > div.list-map-ad.clearfix > div.list-column > section > ol > li:nth-child(1)


    '//*[@id="Search-react-component-0af84deb-7d1f-46d3-b1df-3141e3efca30"]/div/div[3]/div[1]/section/ol/li[1]'

    school_list.find_element_by_xpath()

    print


