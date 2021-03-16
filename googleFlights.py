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

packages_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', '..', '..'))
sys.path.append(os.path.join(packages_path, 'dbConn'))
curr_dir = os.path.dirname(os.path.realpath(__file__))
cd_path = os.path.join(curr_dir, "driver", "chromedriver.exe")

#
# def next_weekday(d, weekday):
#     days_ahead = weekday - d.weekday()
#     if days_ahead <= 0: # Target day already happened this week
#         days_ahead += 7
#     return d + datetime.timedelta(days_ahead)
#
#
# class GoogleFlights:
#
#     def __init__(self, headless=True):
#         self.curr_dir = os.path.dirname(os.path.realpath(__file__))
#         cd_path = os.path.join(self.curr_dir, "driver", "chromedriver.exe")
#         self.chrome_options = Options()
#
#         if headless:
#             self.chrome_options.add_argument("--headless")
#
#         try:
#             self.driver = webdriver.Chrome(executable_path=cd_path, chrome_options=self.chrome_options)
#         except:
#             self.driver = webdriver.Chrome(executable_path=cd_path, chrome_options=self.chrome_options)
#
#         self.base = ""
#         self.skyscanner_path = "https://www.skyscanner.com/transport/flights-from/{FAA_ID}/us/201231"
#         self.airport_list_path = "https://en.wikipedia.org/wiki/List_of_airports_in_the_United_States"
#
#
#     def findDirectFlights(self):

#         for airport in airports:
#             # self.driver.get(self.skyscanner_path)
#             # self.driver.find_element_by_xpath('//*[@id="i8"]/div[2]/div/div/div[1]/div/div/input').clear()
#             # self.driver.find_element_by_xpath('//*[@id="i8"]/div[2]/div/div/div[1]/div/div/input').send_keys(airport)
#             # self.driver.find_element_by_xpath('//*[@id="i8"]/div[2]/div/div/div[1]/div/div/input').send_keys(airport)
#             # self.driver.find_element_by_xpath('//*[@id="i8"]/div[2]/div/div/div[1]/div/div/input').send_keys(airport)
#             #res = requests.get(self.skyscanner_path.format(FAA_ID=airport)).text
#             # self.driver.get(self.skyscanner_path.format(FAA_ID=airport.lower()))
#             # self.driver.find_element_by_xpath('//*[@id="destinations"]/ul')
#             # # self.
#             # print
#             res = requests.get(self.skyscanner_path.format(FAA_ID=airport.lower())).text
#             print
#
#
#
#         print
#
#
#
# def main():
#     google_flights_manager = GoogleFlights(headless=False)
#     google_flights_manager.findDirectFlights()
#     print
#
#
#
# if __name__ == '__main__':
#     main()




def scrape(origin, destination, startdate, days, requests):
    global results

    enddate = datetime.strptime(startdate, '%Y-%m-%d').date() + timedelta(days)
    enddate = enddate.strftime('%Y-%m-%d')

    url = "https://www.kayak.com/flights/" + origin + "-" + destination + "/" + startdate + "/" + enddate + "?sort=bestflight_a&fs=stops=0"
    print("\n" + url)

    chrome_options = webdriver.ChromeOptions()
    agents = ["Firefox/66.0.3", "Chrome/73.0.3683.68", "Edge/16.16299"]
    print("User agent: " + agents[(requests % len(agents))])
    # chrome_options.add_argument('--user-agent=' + agents[(requests % len(agents))] + '"')
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(executable_path=cd_path, options=chrome_options,
                              desired_capabilities=chrome_options.to_capabilities())
    # 20
    driver.implicitly_wait(20)
    driver.get(url)

    # Check if Kayak thinks that we're a bot
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'lxml')

    if soup.find_all('p')[0].getText() == "Please confirm that you are a real KAYAK user.":
        print("Kayak thinks I'm a bot, which I am ... so let's wait a bit and try again")
        driver.close()
        time.sleep(20)
        return "failure"

    time.sleep(20)  # wait 20sec for the page to load

    soup = BeautifulSoup(driver.page_source, 'lxml')

    # get the arrival and departure times
    deptimes = soup.find_all('span', attrs={'class': 'depart-time base-time'})
    arrtimes = soup.find_all('span', attrs={'class': 'arrival-time base-time'})
    meridies = soup.find_all('span', attrs={'class': 'time-meridiem meridiem'})

    deptime = []
    for div in deptimes:
        deptime.append(div.getText()[:-1])

    arrtime = []
    for div in arrtimes:
        arrtime.append(div.getText()[:-1])

    meridiem = []
    for div in meridies:
        meridiem.append(div.getText())

    deptime = np.asarray(deptime)
    deptime = deptime.reshape(int(len(deptime) / 2), 2)

    arrtime = np.asarray(arrtime)
    arrtime = arrtime.reshape(int(len(arrtime) / 2), 2)

    meridiem = np.asarray(meridiem)
    meridiem = meridiem.reshape(int(len(meridiem) / 4), 4)

    # Get the price
    regex = re.compile('Common-Booking-MultiBookProvider (.*)multi-row Theme-featured-large(.*)')
    price_list = soup.find_all('div', attrs={'class': regex})

    price = []
    for div in price_list:
        try:
            price.append(int(re.findall(r"[\$]{1}[\d,]+\.?\d{0,2}", div.text)[0].replace(",", "").replace("$", "")))
        except:
            pass

    try:
        df = pd.DataFrame({"origin": origin,
                           "destination": destination,
                           "startdate": startdate,
                           "enddate": enddate,
                           "price": price,
                           "currency": "USD",
                           "deptime_o": [m + str(n) for m, n in zip(deptime[:, 0], meridiem[:, 0])],
                           "arrtime_d": [m + str(n) for m, n in zip(arrtime[:, 0], meridiem[:, 1])],
                           "deptime_d": [m + str(n) for m, n in zip(deptime[:, 1], meridiem[:, 2])],
                           "arrtime_o": [m + str(n) for m, n in zip(arrtime[:, 1], meridiem[:, 3])]
                           })
    except:
        pass

    results = pd.concat([results, df], sort=False)

    driver.close()  # close the browser

    time.sleep(5)  # wait 15sec until the next request

    return "success"


airport_list = pd.read_html("https://en.wikipedia.org/wiki/List_of_airports_in_the_United_States")[2]
ap_list = airport_list
states_city_mapping = {}
curr_state = ""
states = ap_list[pd.isnull(ap_list["FAA"])]["City"]
states_list = states.values.tolist()

for row in ap_list.iterrows():
    if row[1]["City"] in states_list:
        curr_state = row[1]["City"]
    else:
        states_city_mapping[row[1]["City"]] = curr_state

airports = ap_list["FAA"][~pd.isnull(ap_list["FAA"])].values.tolist()

# Create an empty dataframe
results = pd.DataFrame(
    columns=['origin', 'destination', 'startdate', 'enddate', 'deptime_o', 'arrtime_d', 'deptime_d', 'arrtime_o',
             'currency', 'price'])

requests = 0

originations = ['DFW', 'MKE', 'SRQ']
destinations = [i for i in airports if i not in originations]

# test start dates for 1 week from today, 1 month, 3 months, 6 months, 12 months
startdates = ['2021-01-7']

# should we have an end date start+4days?

for destination in destinations:
    for origination in originations:
        for startdate in startdates:
            scrape(origination, destination, startdate, 4, requests)

# Find the minimum price for each destination-startdate-combination
results_agg = results.groupby(['destination', 'startdate'])['price'].min().reset_index().rename(
    columns={'min': 'price'})

print
