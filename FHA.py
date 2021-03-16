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
FHA_link = "https://entp.hud.gov/idapp/html/hicost1.cfm"

driver.get(FHA_link)
states_list = []
try:
    i = 2
    while 1:
        states_list.append(driver.find_element_by_css_selector('#l_state > option:nth-child({i})'.format(i=i)).text)
        i = i + 1

except:
    pass

cy_list = []
try:
    i = 1
    while 1:
        cy_list.append(driver.find_element_by_css_selector('#l_limit_year > option:nth-child({i})'.format(i=i)).text)
        i = i + 1

except:
    pass

master_df = pd.DataFrame()
for state in states_list:
    for cy in cy_list:
        driver.get(FHA_link)
        #driver.find_element_by_xpath('//*[@id="hicost"]/table/tbody/tr[2]/td[2]/table/tbody/tr[2]/td[2]')
        el = driver.find_element_by_css_selector('#l_state')
        for option in el.find_elements_by_tag_name('option'):
            if option.text == state:
                option.click()  # select() in earlier versions of webdriver
                break

        el = driver.find_element_by_css_selector('#l_limit_year')
        for option in el.find_elements_by_tag_name('option'):
            if option.text == cy:
                option.click()  # select() in earlier versions of webdriver
                break

        el = driver.find_element_by_css_selector('#l_limit_type > option:nth-child(3)').click()
        driver.find_element_by_xpath('/html/body/form/div[1]/input[1]').click()
        print

        el = driver.find_element_by_css_selector('#fluid > table:nth-child(13)').get_attribute(
            'innerHTML').strip().replace("\n", "").replace("\t", "")

        soup = BeautifulSoup(el)
        num_rows = len(soup.find_all("tr"))

        df = []
        for i in range(0, num_rows):
            ip_row = []  # in-progress row we are building
            d_row = soup.find_all("tr")[i].find_all("td")
            num_cols = len(d_row)
            for j in range(0, num_cols):
                ip_row.append(soup.find_all("tr")[i].find_all("td")[j].text.strip())
            df.append(ip_row)
        slave_df = pd.DataFrame(df)

        headers = slave_df.iloc[0]
        slave_df = pd.DataFrame(slave_df.values[1:], columns=headers)

        master_df = master_df.append(slave_df, ignore_index=True)
        print

master_df = master_df.reset_index()
master_df.to_excel("Fannie-Freddie Loan Potentials.xlsx")
