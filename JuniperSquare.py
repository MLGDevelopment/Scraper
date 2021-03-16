import time
import bs4
import pandas as pd
import datetime
import calendar
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from collections import defaultdict


import sys

js_login = "https://mlgcapital.junipersquare.com/login"
js_all_accounts_path = "https://mlgcapital.junipersquare.com/accounts"
js_all_contacts_path = "https://mlgcapital.junipersquare.com/contacts"

js_single_contact_path = "https://mlgcapital.junipersquare.com/contact/"
js_single_contact_accounts = "https://mlgcapital.junipersquare.com/contact/{contact_id}/accounts"

login = "nburmeister@mlgcapital.com"
pwd = "nikMLG$2021"

headless = False

curr_dir = os.path.dirname(os.path.realpath(__file__))
cd_path = os.path.join(curr_dir, "driver", "chromedriver.exe")
chrome_options = Options()

chrome_options.add_argument("user-data-dir=C:\\Users\\nburmeister\\AppData\\Local\\Google\\Chrome\\User Data")

if headless:
    chrome_options.add_argument("--headless")

try:
    driver = webdriver.Chrome(executable_path=cd_path, chrome_options=chrome_options)
except:
    driver = webdriver.Chrome(executable_path=cd_path, chrome_options=chrome_options)


driver.get(js_login)
time.sleep(5)
# email = driver.find_element_by_xpath('//*[@id="signin_tab"]/div/div/form/div[1]/input')
# email.clear()
# email.send_keys(login)
# password = driver.find_element_by_xpath('//*[@id="signin_tab"]/div/div/form/div[2]/input')
# password.clear()
# password.send_keys(pwd)
# driver.find_element_by_xpath('//*[@id="signin_tab"]/div/div/form/div[3]/label/input').click()
try:
    driver.find_element_by_xpath('//*[@id="signin_tab"]/div/div/form/button').click()
    time.sleep(5)
except:
    pass


# scroll down the page



# accounts_table = driver.find_element_by_xpath('//*[@id="account_list"]/table/tbody')

# accounts_data = accounts_table.find_elements(By.TAG_NAME, "tr")
#
# all_acct_ids = []
#
# for acct in accounts_data:
#     acct_id = acct.get_attribute('data-id')
#     all_acct_ids.append(acct_id)
#
#
# # next, visit all account pages
#
# for acct_id in all_acct_ids:
#     path = js_account_path + "/" + str(acct_id)
#     driver.get(path)
#
#     # get all contacts
#     '//div[matches(@id,"contact-map-")]'
#     contacts = driver.find_element_by_xpath('//*[@id="account-contacts"]')
#     contact_items = contacts.find_elements_by_css_selector("*div")
#     contact_items.find_element_by_xpath("//*[contains(@id, 'contact-map-')]")

# go to accounts page
driver.get(js_all_contacts_path)
time.sleep(5)

# todo: scroll

SCROLL_PAUSE_TIME = 5
# Get scroll height
last_height = driver.execute_script("return document.body.scrollHeight")

while True:
    # Scroll down to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Wait to load page
    time.sleep(SCROLL_PAUSE_TIME)

    # Calculate new scroll height and compare with last scroll height
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height


contacts_table = driver.find_element_by_xpath('//*[@id="contact_list"]/table/tbody')
contacts_table = contacts_table.find_elements(By.TAG_NAME, "tr")

all_contact_ids = []

for contact in contacts_table:
    contact_id = contact.get_attribute('data-id')
    all_contact_ids.append(contact_id)

contact_list = []
for contact_id in all_contact_ids:
    contact_info = {}
    path = js_single_contact_path + contact_id
    driver.get(path)
    contact_name = driver.find_element_by_xpath('//*[@id="page-title"]').text
    contact_email = ''
    contact_phone = ''
    contact_work = ''

    for i in range(5):
        div_index = i+1
        try:
            label = driver.find_element_by_xpath('// *[ @ id = "contact_details"] / div[1] / div[{pos}] / div[1]'.format(pos=div_index)).text
        except:
            break

        if label == 'Email':
            contact_email = driver.find_element_by_xpath('// *[ @ id = "contact_details"] / div[1] / div[{pos}] / div[2]'.format(pos=div_index)).text

        if label == 'Phone':
            contact_phone = driver.find_element_by_xpath('// *[ @ id = "contact_details"] / div[1] / div[{pos}] / div[2]'.format(pos=div_index)).text

        # if label == 'Work':
        #     contact_work = driver.find_element_by_xpath('// *[ @ id = "contact_details"] / div[1] / div[{pos}] / div[2]'.format(pos=div_index)).text

    rows = driver.find_elements_by_xpath('//div[@class="row"]/div')
    sf_id = ''
    contact_owner = ''
    for i, row in enumerate(rows):
        if row.text == 'SF Contact ID':
            sf_id = rows[i+1].text

        if row.text == 'Contact Owner':
            contact_owner = rows[i+1].text

    contact_info['id'] = contact_id
    contact_info['contact_name'] = contact_name
    contact_info['contact_email'] = contact_email
    contact_info['work_phone'] = contact_work
    contact_info['mobile_phone'] = contact_phone
    contact_info['salesforce_id'] = sf_id
    contact_info['contact_owner'] = contact_owner
    contact_list.append(contact_info)

    # # todo: remove
    # if len(contact_list) > 4:
    #     break

master_df = pd.DataFrame()
for contact in contact_list:
    path = js_single_contact_accounts.format(contact_id=contact['id'])
    driver.get(path)

    try:
        accounts_table = driver.find_element_by_xpath('//*[@id="contact_accounts"]/table/tbody')
        accounts_data = accounts_table.find_elements(By.TAG_NAME, "tr")
    except:
        accounts_data = []

    all_acct_ids = []
    for acct in accounts_data:
        acct_id = acct.get_attribute('data-id')
        if acct_id is not None:
            all_acct_ids.append(acct_id)

    contact['account_list'] = all_acct_ids
    df = pd.DataFrame.from_dict(contact, orient='columns')
    master_df = master_df.append(df)
print
master_df.to_excel('juniper_square_mapping.xlsx')