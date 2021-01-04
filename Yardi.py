# -*- coding: utf-8 -*-
# Author: Nik Burmeister
import time
import bs4
import pandas as pd
import datetime
import calendar
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys

packages_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', '..', '..'))
sys.path.append(os.path.join(packages_path, 'dbConn'))


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)


class Yardi:

    def __init__(self, headless=True):
        self.curr_dir = os.path.dirname(os.path.realpath(__file__))
        cd_path = os.path.join(self.curr_dir, "driver", "chromedriver.exe")
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument("--headless")

        try:
            self.driver = webdriver.Chrome(executable_path=cd_path, chrome_options=self.chrome_options)
        except:
            self.driver = webdriver.Chrome(executable_path=cd_path, chrome_options=self.chrome_options)

        self.base = ""

    def login(self, username, password, login_link):
        """
        METHOD TO LOG INTO YARDI
        :param username:
        :param password:
        :param login_link:
        :return:
        """
        try:
            self.driver.get(login_link)
            username_field = self.driver.find_element_by_id("Username")
            username_field.clear()
            username_field.send_keys(username)
            self.driver.find_element_by_id("Password_Text").click()
            self.driver.find_element_by_id("Password").send_keys(password)
            self.driver.find_element_by_id("cmdLogin1").click()
            return 1
        except:
            return 0

    def valiant_yardi_login(self):
        yardi_login_url = "https://www.yardiasp13.com/47310settlement/pages/LoginAdvanced.aspx"
        self.base = "https://www.yardiasp13.com/47310settlement/pages/"
        valiant_username = "nburmeister"
        valiant_password = "Winter19!"
        return self.login(valiant_username, valiant_password, yardi_login_url)

    def mlg_yardi_login(self):
        yardi_login_url = "https://www.yardiasptx11.com/65876mlgcapital/pages/LoginAdvanced.aspx"
        self.base = "https://www.yardiasptx11.com/65876mlgcapital/pages/"
        mlg_username = "mlgco"
        mlg_password = "mgmt2019"
        return self.login(mlg_username, mlg_password, yardi_login_url)

    def T12_Month_Statement(self, property, book, account_tree, period_start, period_end, acct_codes, export=False):

        yardi_financial_analytics_url = self.base + "GlrepFinancial.aspx"
        self.driver.get(yardi_financial_analytics_url)
        self.driver.find_element_by_id("PropertyID_LookupCode").clear()
        self.driver.find_element_by_id("PropertyID_LookupCode").send_keys(property)
        self.driver.find_element_by_id("BookID_LookupCode").clear()
        self.driver.find_element_by_id("BookID_LookupCode").send_keys(book)
        self.driver.find_element_by_id("TreeID_LookupCode").clear()
        self.driver.find_element_by_id("TreeID_LookupCode").send_keys(account_tree)
        self.driver.find_element_by_id("FromMMYY_TextBox").clear()
        self.driver.find_element_by_id("FromMMYY_TextBox").send_keys(period_start)
        self.driver.find_element_by_id("ToMMYY_TextBox").clear()
        self.driver.find_element_by_id("ToMMYY_TextBox").send_keys(period_end)

        if export:
            self.driver.find_element_by_id("Excel_Button").click()
            return 1

        self.driver.find_element_by_id("Display_Button").click()

        soup = BeautifulSoup(self.driver.page_source)
        financials = soup.find(id="TableWriter1")

        headers = []
        data = []

        for index, row in enumerate(financials.findAll('tr')):
            if index == 0:
                t_headers = financials.findAll('tr')[0].find_all('th')
                for h in t_headers:
                    headers.append(h.text.strip())
            else:
                line_item = row.findAll('td')
                line_data = []
                for i in line_item:
                    if isinstance(i, bs4.element.Tag):
                        try:
                            val = i.text.strip()
                            try:
                                val = float(i.text.strip().replace(",", ""))
                            except ValueError:
                                pass
                            line_data.append(val)
                        except AttributeError:
                            print("Error")
                data.append(line_data)

        df = pd.DataFrame(data=data)
        headers[0] = "Item"
        headers = [datetime.datetime.strptime(i, "%b %Y") for i in headers[2:-1]]
        headers = [datetime.date(d.year, d.month, calendar.monthrange(d.year, d.month)[-1]) for d in headers]
        headers.insert(0, "")
        headers.insert(0, "Item")
        del df[14]
        df.columns = headers
        df = df.set_index("Item")
        yardi_codes = [i.yardi_acct_code for i in acct_codes]
        filtered_df = df.iloc[df.index.isin(yardi_codes)]
        ret_df = filtered_df.iloc[:, 1:].T
        return ret_df

    def get_multifamily_stats(self, yardi_property_id, as_of_date):
        yardi_residential_reports_url = self.base + "ResReportSummary.aspx"
        self.driver.get(yardi_residential_reports_url)
        time.sleep(2)
        self.driver.find_element_by_css_selector("#ReportType_DropDownList").send_keys("Unit Statistic \nselect")
        self.driver.find_element_by_css_selector("#PropLookup_LookupCode").clear()
        self.driver.find_element_by_css_selector("#PropLookup_LookupCode").send_keys(yardi_property_id)
        self.driver.find_element_by_css_selector("#Date2_TextBox").clear()
        self.driver.find_element_by_css_selector("#Date2_TextBox").send_keys(str(as_of_date))
        self.driver.find_element_by_css_selector("#Display_Button").click()
        time.sleep(2)

        soup = BeautifulSoup(self.driver.page_source)
        unit_stats = soup.find_all('table')[1]
        rows = unit_stats.find_all('tr')[3:]

        headers = [i.text for i in rows[0].find_all('th')]
        records = []
        for row in rows:
            columns = row.find_all('td')
            if columns:
                record = []
                for column in columns:
                    record.append(column.text.strip())
                if len(record) == len(headers):
                    records.append(record)

        occupancy = self.driver.find_element_by_xpath("/html/body/form/div[5]/div[2]/table/tbody/tr[4]/td[3]")
        occupancy = float(occupancy.text)/100
        market_rent = self.driver.find_element_by_xpath("/html/body/form/div[5]/div[1]/table/tbody/tr[16]/td[7]")
        market_rent = float(market_rent.text)
        occupied_rent = self.driver.find_element_by_xpath("/html/body/form/div[5]/div[1]/table/tbody/tr[16]/td[8]")
        occupied_rent = float(occupied_rent.text)

        self.driver.find_element_by_css_selector("#ReportType_DropDownList").send_keys("Projected Occupancy \nselect")
        self.driver.find_element_by_css_selector("#Display_Button").click()
        _60_day_trend = self.driver.find_element_by_xpath("/html/body/form/div[5]/div[1]/table/tbody/tr[11]/td[6]")
        _60_day_trend = float(_60_day_trend.text) / 100
        self.driver.find_element_by_css_selector("#ReportType_DropDownList").send_keys("Aged Receivables \nselect")
        time.sleep(.75)
        self.driver.find_element_by_css_selector("#SummarizeBy_DropDownList").send_keys("Property \nselect")
        time.sleep(.75)
        self.driver.find_element_by_css_selector("#Display_Button").click()
        time.sleep(2.25)
        _30_day_ar = self.driver.find_element_by_xpath("/html/body/form/div[5]/div[1]/table/tbody/tr[6]/td[4]")
        _30_day_ar = float(_30_day_ar.text.replace(",", ""))
        _all_ar = self.driver.find_element_by_xpath("/html/body/form/div[5]/div[1]/table/tbody/tr[6]/td[9]")
        _all_ar = float(_all_ar.text.replace(",", ""))

        res = {"occupancy": occupancy,
               "60_day_trend": _60_day_trend,
               "occupied_rent": occupied_rent,
               "market_rent": market_rent,
               "30_day_AR": _30_day_ar,
               "total_AR": _all_ar}

        return res

    def pull_multifamily_stats(self, properties, start, end):
        t_span = pd.date_range(start, end, freq='2W').strftime("%m/%d/%Y").tolist()
        df = pd.DataFrame()
        for y_property in properties:
            for _date in t_span:
                res = self.get_multifamily_stats(y_property.yardi_id, _date)
                res["name"] = y_property.name
                res["period_ending"] = _date
                df.append(res, ignore_index=True)

    def rent_roll(self, yardi_id, as_of_date):
        yardi_residential_reports_url = self.base + "ResReportSummary.aspx"
        self.driver.get(yardi_residential_reports_url)
        time.sleep(2)
        self.driver.find_element_by_css_selector("#ReportType_DropDownList").send_keys("Rent Roll with Lease Charges \nselect")
        self.driver.find_element_by_css_selector("#PropLookup_LookupCode").clear()
        self.driver.find_element_by_css_selector("#PropLookup_LookupCode").send_keys(yardi_id)
        self.driver.find_element_by_css_selector("#Date2_TextBox").clear()
        as_of_date = "{month}/{day}/{year}".format(month=as_of_date.month, day=as_of_date.day, year=as_of_date.year)
        self.driver.find_element_by_css_selector("#Date2_TextBox").send_keys(str(as_of_date))
        self.driver.find_element_by_id("Excel_Button").click()
        return 1

    def download_mf_T12(self, yardi_id, start, end):
        self.T12_Month_Statement(yardi_id, 'accrual', '', start, end, [], export=True)

    def download_mf_RR(self, yardi_id, as_of_date):
        self.rent_roll(yardi_id, as_of_date)

    def yardi_excel_pull(self, properties, start, end, as_of_date):
        for prop in properties:
            self.download_mf_T12(prop[1], start, end)
            time.sleep(1)
            self.download_mf_RR(prop[1], as_of_date)
            time.sleep(0.5)


def main():
    yardi_manager = Yardi(headless=True)
    yardi_manager.valiant_yardi_login()
    yardi_manager.pull_multifamily_stats()


if __name__ == '__main__':
    main()
