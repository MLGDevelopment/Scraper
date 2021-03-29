# -*- coding: utf-8 -*-
# Author: Nik Burmeister
import time
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import random


def extract_assinged_school_data(page_divs, indicies):
    """

    :param page_divs:
    :param indicies:
    :return:
    """
    schools = []
    for index in indicies:
        s_offset = 0
        a_offset = 4
        p_offset = 5
        if 'Currently unrated' in page_divs[index+1].text:
            a_offset = 3
            p_offset = 4

        if 'award' in page_divs[index + 4].text:
            s_offset = 2

        rating = page_divs[index+2].text
        address = page_divs[index+a_offset+s_offset].text
        students = page_divs[index+p_offset+s_offset].text
        s_type = students.split(",")[0]
        g_range = students.split(",")[1].split("|")[0]
        n_students = int(students.split("|")[1].split("students")[0].replace(",", ""))
        schools.append([rating, address, s_type, g_range, n_students])

    return schools


SLEEP_TIME = 3


class GreatSchools():

    def __init__(self, headless=False):
        self.headless = False
        self.curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.cd_path = os.path.join(self.curr_dir, "driver", "chromedriver.exe")
        self.chrome_options = Options()

        self.base = base = "https://www.greatschools.org/"

        if headless:
            self.chrome_options.add_argument("--headless")

        try:
            self.driver = webdriver.Chrome(executable_path=self.cd_path, chrome_options=self.chrome_options)
        except:
            self.driver = webdriver.Chrome(executable_path=self.cd_path, chrome_options=self.chrome_options)

    def open_public_schools(self):
        self.public_schools_path = os.path.join(self.curr_dir, "data", "schools", "Public_Schools.xlsx")
        self.public_schools_df = pd.read_excel(self.public_schools_path)
        self.public_schools_df['index'] = self.public_schools_df['LATITUDE'].astype(str) + self.public_schools_df[
            'LONGITUDE'].astype(str)
        self.public_schools_df.set_index('index', inplace=True)

        self.public_schools_df['full_address'] = self.public_schools_df['ADDRESS'].astype(str) + ", " + \
                                                  self.public_schools_df['CITY'] + ", " + \
                                                  self.public_schools_df['STATE'] + " " + self.public_schools_df[
                                                      'ZIP'].astype(str)

    def open_private_schools(self):
        self.private_schools_path = os.path.join("data", "schools", "Private_Schools.xlsx")
        self.private_schools_df = pd.read_excel(self.private_schools_path)
        self.private_schools_df['index'] = self.private_schools_df['LATITUDE'].astype(str) + self.private_schools_df['LONGITUDE'].astype(str)
        self.private_schools_df.set_index('index', inplace=True)

        self.private_schools_df['full_address'] = self.private_schools_df['ADDRESS'].astype(str) + ", " + self.private_schools_df['CITY'] + ", " + \
                                         self.private_schools_df['STATE'] + " " + self.private_schools_df['ZIP'].astype(str)

    def extract_individual_ratings(self, data):
        split_data = data.text.split("\n")
        split_data = [i.strip() for i in split_data]



        schools = []
        while split_data:
            rating_offset = 0
            name_offset = 2
            address_offset = 3
            info_offset = 4

            curr_data = split_data.pop(0)
            if 'Assigned school' in curr_data:
                try:
                    rating = split_data[rating_offset]
                    name = split_data[name_offset]
                    if 'award' in split_data[address_offset]:
                        address_offset = 4
                        info_offset = 5
                    address = split_data[address_offset]
                    info_ = split_data[info_offset]
                    s_type = info_ .split(",")[0]
                    g_range = info_ .split(",")[1].split("|")[0]
                    n_students = int(info_ .split("|")[1].split("students")[0].replace(",", ""))
                    schools.append([rating, name, address, s_type, g_range, n_students])
                except:
                    print

            while split_data:
                curr = split_data.pop(0)
                if 'Homes for sale' in curr:
                    break

        return schools

    def run_private_schools(self):

        self.driver.get(self.base)
        self.open_private_schools()
        pri_schools_df = self.private_schools_df
        driver = self.driver

        mapping = {}

        master = pd.DataFrame()
        for school in pri_schools_df.iterrows():
            driver.get(self.base)
            school_address = school[1]['full_address']
            driver.find_element_by_xpath('//*[@id="home-page"]/div[1]/div/section/div[1]/div[1]/div/div/div/div[1]/form/input').send_keys(school_address)
            time.sleep(.5)
            driver.find_element_by_xpath('//*[@id="home-page"]/div[1]/div/section/div[1]/div[1]/div/div/div/div[1]/form/input').send_keys(Keys.ENTER)
            time.sleep(SLEEP_TIME*random.random())
            page_divs = driver.find_elements_by_css_selector("div")

            divs_with_data = []
            for i, div in enumerate(page_divs):
                if div.text != "":
                    divs_with_data.append(div)

            indicies = []
            for i, div in enumerate(divs_with_data):
                if div.text == 'Assigned school':
                    indicies.append(i)

            if indicies:
                dat = extract_assinged_school_data(divs_with_data, indicies)
                mapping[school[0]] = dat
            else:
                mapping[school[0]] = None

            for key in mapping.keys():
                if mapping[key]:
                    temp_df = pd.DataFrame(mapping[key], columns=["Rating", "Address", "Type", "Range", "Students"])
                    temp_df['uid'] = key
                    master = master.append(temp_df)

            master.to_excel("private_school_data.xlsx")

    def run_public_schools(self):

        self.driver.get(self.base)
        self.open_public_schools()
        public_schools_df = self.public_schools_df
        driver = self.driver

        mapping = {}

        master = pd.DataFrame()
        for school in public_schools_df.iterrows():
            driver.get(self.base)
            school_address = school[1]['full_address']
            driver.find_element_by_xpath('//*[@id="home-page"]/div[1]/div/section/div[1]/div[1]/div/div/div/div[1]/form/input').send_keys(school_address)
            time.sleep(0.5)
            driver.find_element_by_xpath('//*[@id="home-page"]/div[1]/div/section/div[1]/div[1]/div/div/div/div[1]/form/input').send_keys(Keys.ENTER)
            sleep_floor = 2.75
            r_sleep = random.random() + sleep_floor
            time.sleep(r_sleep)
            # page_divs = driver.find_elements_by_css_selector("div")

            try:
                page_ols = driver.find_elements_by_css_selector("ol")[0]
            except:
                driver.find_element_by_xpath(
                    '//*[@id="home-page"]/div[1]/div/section/div[1]/div[1]/div/div/div/div[1]/form/input').send_keys(
                    Keys.ENTER)

            schools = self.extract_individual_ratings(page_ols)
            mapping[school[0]] = schools

            for key in mapping.keys():
                if mapping[key]:
                    temp_df = pd.DataFrame(mapping[key], columns=["Rating", "Name", "Address", "Type", "Range", "Students"])
                    temp_df['uid'] = key
                    master = master.append(temp_df)
                    master.drop_duplicates('Address', 'first', inplace=True)
                    master.reset_index(inplace=True, drop=True)

            master.to_excel("public_school_data.xlsx")


gss = GreatSchools()
gss.run_public_schools()
