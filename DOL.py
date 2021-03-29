import time
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


headless = False

curr_dir = os.path.dirname(os.path.realpath(__file__))
cd_path = os.path.join(curr_dir, "driver", "chromedriver.exe")
chrome_options = Options()

# chrome_options.add_argument("user-data-dir=C:\\Users\\nburmeister\\AppData\\Local\\Google\\Chrome\\User Data")

if headless:
    chrome_options.add_argument("--headless")

try:
    driver = webdriver.Chrome(executable_path=cd_path, chrome_options=chrome_options)
except:
    driver = webdriver.Chrome(executable_path=cd_path, chrome_options=chrome_options)

base = "https://oui.doleta.gov/unemploy/claims.asp"
driver.get(base)
curr_dir = os.path.join(os.path.dirname(__file__))

driver.find_element_by_xpath('//*[@id="content"]/table/tbody/tr[1]/td/input[2]').click()
driver.find_element_by_xpath('//*[@id="states"]')

states_list = []
try:
    i = 1
    while 1:
        state = driver.find_element_by_xpath('/html/body/div/div[2]/div[2]/table/tbody/tr[5]/td/div/select/option[{0}]'.format(i)).text
        states_list.append(state)
        i = i + 1
except:
    pass


master = pd.DataFrame()
for state in states_list:
    driver.get(base)
    driver.find_element_by_xpath('//*[@id="content"]/table/tbody/tr[1]/td/input[2]').click()
    el = driver.find_element_by_xpath('//*[@id="states"]')
    for option in el.find_elements_by_tag_name('option'):
        if option.text == state:
            option.click()
            break

    driver.find_element_by_xpath('//*[@id="content"]/table/tbody/tr[6]/td/input').click()
    time.sleep(2)
    tbl = driver.find_element_by_xpath('//*[@id="content"]/table').get_attribute('outerHTML')
    df = pd.read_html(tbl)
    df = pd.DataFrame(df[0].iloc[2:, :].values.tolist(), columns=df[0].iloc[1, :].values.tolist())
    df = df.iloc[:, :7]
    master = master.append(df)
master.reset_index(inplace=True, drop=True)
master.to_excel('DOL State Unemployment Insurance Claims.xlsx')
print