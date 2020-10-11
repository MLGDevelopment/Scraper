from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
import json
from datetime import date
import datetime
from selenium import webdriver
import pandas as pd
import os
import sys
import time
import traceback
import usaddress
import random

packages_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..'))
sys.path.append(os.path.join(packages_path, 'dbConn'))
from axioDB import session, RentComp, AxioProperty, AxioPropertyOccupancy


class AxioScraper:

    def __init__(self, headless=True):
        self.headless = headless
        self.curr_dir = os.path.dirname(os.path.realpath(__file__))
        cd_path = os.path.join(self.curr_dir, "driver", "chromedriver.exe")
        self.chrome_options = Options()
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("start-maximized")
        self.chrome_options.add_argument("enable-automation")
        self.chrome_options.add_argument("--disable-infobars")
        self.chrome_options.add_argument("--disable-browser-side-navigation")
        self.chrome_options.add_argument("--disable-gpu")

        if headless:
            self.chrome_options.add_argument("--headless")

        try:
            self.driver = webdriver.Chrome(executable_path=cd_path, chrome_options=self.chrome_options)
        except:
            self.driver = webdriver.Chrome(executable_path=cd_path, chrome_options=self.chrome_options)

        self.login_path = "https://axio.realpage.com/Home"
        self.market_trends_path = "https://axio.realpage.com/Report/MarketTrendSearch"
        self.property_report_path = "https://axio.realpage.com/PropertyReport/UnitMix/"
        self.logged_in = False
        self.base = ""
        self.current_id = -1
        self.property_occupancy = -1
        self.property_details = - 1
        self.unit_mix = - 1

    def reboot_driver(self):
        self.driver.quit()
        time.sleep(2)
        cd_path = os.path.join(self.curr_dir, "driver", "chromedriver.exe")
        self.chrome_options = Options()
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("start-maximized")
        self.chrome_options.add_argument("enable-automation")
        self.chrome_options.add_argument("--disable-infobars")
        self.chrome_options.add_argument("--disable-browser-side-navigation")
        self.chrome_options.add_argument("--disable-gpu")

        if self.headless:
            self.chrome_options.add_argument("--headless")

        try:
            self.driver = webdriver.Chrome(executable_path=cd_path, chrome_options=self.chrome_options)
        except:
            self.driver = webdriver.Chrome(executable_path=cd_path, chrome_options=self.chrome_options)
        self.mlg_axio_login()
        return 1

    def login(self, username, password, login_link):
        """
        METHOD TO LOG INTO YARDI
        :param username:
        :param password:
        :param login_link:
        :return:
        """
        # todo: error check
        try:
            self.driver.get(login_link)
            username_field = self.driver.find_element_by_id("username")
            username_field.clear()
            username_field.send_keys(username)
            self.driver.find_element_by_id("password").click()
            self.driver.find_element_by_id("password").send_keys(password)
            self.driver.find_element_by_id("btnSignIn").click()
            self.logged_in = True
            return 1
        except:
            return 0

    def mlg_axio_login(self):
        with open(os.path.join(self.curr_dir, "pwd.json")) as json_file:
            data = json.load(json_file)
            mlg_username = data["axio_login"]["username"]
            mlg_password = data["axio_login"]["password"]
        return self.login(mlg_username, mlg_password, self.login_path)

    def pull_national_data(self):
        time.sleep(3)
        if self.logged_in:
            self.driver.get(self.market_trends_path)
            time.sleep(3.5)
            frequency = self.driver.find_element_by_xpath("//*[@id='body-container']/div/div[2]/div[1]/table/tbody/tr[1]/td[1]/span")
            # frequency.send_keys("Quarterly\nselect")
            frequency.send_keys("Annual\nselect")

            report_level = self.driver.find_element_by_xpath("//*[@id='body-container']/div/div[2]/div[1]/table/tbody/tr[1]/td[2]/span")
            report_level.send_keys("National\nselect")

            start_quarter = self.driver.find_element_by_xpath("//*[@id='body-container']/div/div[2]/div[1]/table/tbody/tr[1]/td[3]/span[1]")
            start_quarter.send_keys("1st Quarter\nselect")

            start_year = self.driver.find_element_by_xpath("//*[@id='body-container']/div/div[2]/div[1]/table/tbody/tr[1]/td[3]/span[2]")
            start_year.send_keys("1995\nselect")

            end_quarter = self.driver.find_element_by_xpath("//*[@id='body-container']/div/div[2]/div[1]/table/tbody/tr[1]/td[4]/span[1]")
            end_quarter.send_keys("2nd Quarter\nselect")

            end_year = self.driver.find_element_by_xpath("//*[@id='body-container']/div/div[2]/div[1]/table/tbody/tr[1]/td[4]/span[2]")
            end_year.send_keys("2019\nselect")

            self.driver.find_element_by_id("btnMarketSearch").click()

            time.sleep(3)

            # now get table

            d_table = self.driver.find_element_by_xpath("//*[@id='period-wrap-table']")
            columns = d_table.find_elements(By.TAG_NAME, "td")

            index_col = columns[0].text.split("\n")
            m_list = [[i] for i in index_col]

            data_col = columns[1].text.split("\n")
            num_rows = len(index_col)

            s_rows = ["SUMMARY",
                      "PERFORMANCE TREND",
                      "Asking Rent",
                      "Effective Rent",
                      "Physical Occupancy Rate",
                      "Rental Revenue Impact",
                      "Concessions",
                      "Portfolio Attributes",
                      "SUPPLY AND DEMAND TREND",
                      "Job Growth",
                      "Residential Permitting",
                      "Job Growth Ratio",
                      "Single Family Home Affordability",
                      ]

            actual_data_length = len([i for i in index_col if i not in s_rows])

            quarter = 0
            r_count = 0
            d_count = 0
            while True:

                if r_count < num_rows and index_col[r_count] in s_rows:
                    m_list[r_count].append("")
                    r_count += 1
                else:
                    if r_count < num_rows and d_count < num_rows:
                        m_list[r_count].append(data_col[actual_data_length*quarter+d_count])
                        r_count += 1
                        d_count += 1
                    else:
                        if actual_data_length*quarter+d_count >= len(data_col):
                            break
                        r_count = 0
                        d_count = 0
                        quarter += 1
            pd.DataFrame(m_list)

    def navigate_to_property_report(self, _id):
        """
        NAVIGATE TO PROPERTY PAGE, WAIT UNTIL PAGE LOADS AND RETRY UNTIL WE LAND
        :param _id:
        :return:
        """
        url = os.path.join(self.property_report_path, str(_id))
        delay = 2
        r_count = 0
        while 1:
            try:
                self.driver.get(url)
                r_count += 1
                element_present = EC.presence_of_element_located((By.ID, 'property-name'))
                try:
                    WebDriverWait(self.driver, delay).until(element_present)
                    return 1
                except TimeoutException:
                    # todo: check for errors
                    try:
                        if self.driver.find_element_by_xpath("/html/body/hgroup/h1").text == "Error.":
                            # there is no property page, return 0
                            print("Error Page Not Found for {_id}".format(_id=_id))
                            return 0
                        elif r_count == 3:
                            # exhausted
                            print("Requests Exhausted for {_id}".format(_id=_id))
                            return 0
                    except NoSuchElementException:
                        print("Error Page Not Found for {_id}".format(_id=_id))
                    except TimeoutException:
                        print("rebooting driver")
                        self.reboot_driver()
                        time.sleep(1)
            except TimeoutException:
                print("rebooting driver")
                self.reboot_driver()
                time.sleep(1)
            except:
                traceback.print_exc()
                exit(1)


    def get_property_details(self, _id):
        """
        must call navigate_to_property_report prior to call
        :return:
        """
        _id = str(_id)
        self.navigate_to_property_report(_id)

        res = []
        try:
            res = session.query(AxioProperty).filter(AxioProperty.property_id == _id).one()
            print("Axio Property already Indexed!")
        except NoResultFound:
            print("Axio Property {_id} not in Database - Adding!".format(_id=_id))

        try:
            if not res:
                property_details = dict()

                property_details["property_id"] = _id

                property_details["property_address"] = self.driver.find_element_by_css_selector(
                    "#body-container > div > div.col-md-10 > div.page-header > table > tbody > tr > td:nth-child(1) > "
                    "h2 > small").text

                parsed_addr = usaddress.parse(property_details["property_address"])

                property_details["property_street"] = parsed_addr[0][0] + " " + " ".join(
                    parsed_addr[i][0] for i, v in enumerate(parsed_addr) if parsed_addr[i][1] == 'StreetName')

                try:
                    property_details["property_city"] = [parsed_addr[i][0]
                                                         for i, v in enumerate(parsed_addr)
                                                         if parsed_addr[i][1] == 'PlaceName'][0].replace(",", "")
                except IndexError:
                    property_details["property_city"] = None

                try:
                    property_details["property_state"] = [parsed_addr[i][0]
                                                          for i, v in enumerate(parsed_addr)
                                                          if parsed_addr[i][1] == 'StateName'][0].replace(",", "")
                except IndexError:
                    property_details["property_state"] = None

                try:
                    property_details["property_zip"] = [parsed_addr[i][0]
                                                        for i, v in enumerate(parsed_addr)
                                                        if parsed_addr[i][1] == 'ZipCode'][0]
                except IndexError:
                    property_details["property_zip"] = None

                try:
                    property_details["property_name"] = self.driver.find_element_by_css_selector("#property-name").text
                except NoSuchElementException:
                    property_details["property_name"] = None

                try:
                    property_details["property_owner"] = self.driver.find_element_by_css_selector(
                        "#body-container > div > div.col-md-10 > div.page-header > table > tbody >"
                        " tr > td:nth-child(2) > dl >dd:nth-child(4)").text
                except NoSuchElementException:
                    property_details["property_owner"] = None

                try:
                    property_details["property_management"] = self.driver.find_element_by_css_selector(
                        "#body-container > div > div.col-md-10 > div.page-header > table >"
                        " tbody > tr > td:nth-child(2) > dl > "
                        "dd:nth-child(6)").text
                except NoSuchElementException:
                    property_details["property_management"] = None

                try:
                    property_details["year_built"] = int(self.driver.find_element_by_css_selector(
                        "#tab_unitmix > table:nth-child(3) > tbody > tr:nth-child(1) > td:nth-child(4)").text.split(":")[1])
                except NoSuchElementException:
                    property_details["year_built"] = None
                except ValueError:
                    property_details["year_built"] = None

                try:
                    property_details["total_units"] = int(self.driver.find_element_by_css_selector(
                        "#tab_unitmix > table:nth-child(3) > tbody > tr:nth-child(1) > td:nth-child(1)").text.split(
                        ":")[1].replace(",", ""))
                except NoSuchElementException:
                    property_details["total_units"] = None
                except ValueError:
                    property_details["total_units"] = None

                try:
                    area_per_unit = int(self.driver.find_element_by_css_selector(
                        "#tab_unitmix > table:nth-child(3) > tbody > tr:nth-child(3) > td:nth-child(1)").text.split(
                        ":")[1].replace(",", ""))
                except NoSuchElementException:
                    area_per_unit = 0
                except ValueError:
                    area_per_unit = 0

                try:
                    property_details["property_website"] = self.driver.find_element_by_css_selector(
                        "#body-container > div > div.col-md-10 > div.page-header > table > tbody > tr > "
                        "td:nth-child(2) > dl >"
                        " dd:nth-child(8) > a").get_attribute("href")
                except NoSuchElementException:
                    property_details["property_website"] = None

                try:
                    property_details["property_asset_grade_market"] = self.driver.find_element_by_css_selector(
                        "#body-container > div > div.col-md-2 > div > a:nth-child(4) > p:nth-child(2)").text
                except NoSuchElementException:
                    property_details["property_asset_grade_market"] = None

                try:
                    property_details["property_asset_grade_submarket"] = self.driver.find_element_by_css_selector(
                        "#body-container > div > div.col-md-2 > div > a:nth-child(5) > p:nth-child(2)").text
                except NoSuchElementException:
                    property_details["property_asset_grade_submarket"] = None

                try:
                    property_details["total_square_feet"] = area_per_unit * property_details["total_units"]
                except NoSuchElementException:
                    property_details["total_square_feet"] = None

                try:
                    property_details["msa"] = self.driver.find_element_by_css_selector(
                        "#body-container > div > div.col-md-2 > div > a:nth-child(2) > p:nth-child(2)").text
                except NoSuchElementException:
                    property_details["msa"] = None

                try:
                    property_details["submarket_name"] = self.driver.find_element_by_css_selector(
                        "#body-container > div > div.col-md-2 > div > a:nth-child(3) > p:nth-child(2)").text
                except NoSuchElementException:
                    property_details["submarket_name"] = None

                try:
                    property_details["survey_date"] = self.driver.find_element_by_css_selector(
                        "#body-container > div > div.col-md-2 > div > a:nth-child(7) > p:nth-child(2)").text
                except NoSuchElementException:
                    property_details["survey_date"] = None

                # todo: add error checking
                self.driver.get("https://axio.realpage.com/PropertyReport/Transactions/{id}".format(id=_id))
                
                try:
                    property_details["status"] = self.driver.find_element_by_css_selector(
                        "body > div.container-fluid > div:nth-child(4) >"
                        " div > table > tbody > tr:nth-child(1) > td:nth-child(2)").text.split(":")[1].strip()
                except NoSuchElementException:
                    property_details["status"] = None

                try:
                    property_details["last_sale_date"] = self.driver.find_element_by_css_selector(
                        "body > div.container-fluid > div:nth-child(2) > div > "
                        "table > tbody > tr:nth-child(1) > td:nth-child(2)").text.split(":")[1]
                    if property_details["last_sale_date"] == "":
                        property_details["last_sale_date"] = None
                except NoSuchElementException:
                    property_details["last_sale_date"] = None

                try:
                    self.driver.find_element_by_css_selector(
                        "body > div.container-fluid > div:nth-child(2) > div > table > "
                        "tbody > tr:nth-child(4) > td:nth-child(1)").text.split(":")[1]
                except NoSuchElementException:
                    property_details["last_sale_price"] = None

                try:
                    property_details["parcel_number"] = self.driver.find_element_by_css_selector(
                        "body > div.container-fluid > div:nth-child(2) >"
                        " div > table > tbody > tr:nth-child(3) > td:nth-child(3)").text.split(":")[1].strip()
                except NoSuchElementException:
                    property_details["parcel_number"] = None

                try:
                    property_details["levels"] = int(self.driver.find_element_by_css_selector(
                        "body > div.container-fluid > div:nth-child(4) > div > table > tbody >"
                        " tr:nth-child(1) > td:nth-child(3)").text.split(":")[1])
                except NoSuchElementException:
                    property_details["levels"] = None

                axp = AxioProperty(**property_details)
                self.property_details = axp
                try:
                    session.add(axp)
                    session.commit()
                except IntegrityError:
                    session.rollback()
                    session.flush()
            else:
                self.property_details = res

        except Exception:
            print("FAILED ON PROPERTY ID {ID}".format(ID=_id))
            traceback.print_exc()
            return 0

        return 1

    def get_property_data(self, _id, cache_res=True):
        """
        must call navigate_to_property_report prior to call
        :param _id:
        :param cache_res:
        :param return_res:
        :return:
        """
        _id = str(_id)
        self.navigate_to_property_report(_id)

        try:
            tbl = self.driver.find_element_by_css_selector("#tab_unitmix > table:nth-child(5)")
        except NoSuchElementException:
            tbl = []

        unit_report_list = []
        for j, row in enumerate(tbl.find_elements_by_css_selector('tr')):
            tbl_width = len(row.text.split(" "))
            if tbl_width >= 7:
                d_tbl = row.find_elements_by_tag_name('td')
                if bool(d_tbl):
                    unit_report = dict()
                    unit_report["property_id"] = _id
                    unit_report["date_added"] = str(date.today())
                    unit_report["unit_mix_id"] = j - 1
                    for i, cell in enumerate(d_tbl):
                        if i == 0:
                            unit_report["type"] = cell.text.replace("/", "B/")
                        elif i == 1:
                            unit_report["area"] = cell.text.replace(",", "")
                            pass
                        elif i == 2:
                            unit_report["quantity"] = cell.text.replace(",", "")
                            pass
                        elif i == 5:
                            unit_report["avg_market_rent"] = cell.text.replace("$", "").replace(",", "")
                        elif i == 9:
                            unit_report["avg_effective_rent"] = cell.text.replace("$", "").replace(",", "")

                    if bool(unit_report):
                        unit_report_list.append(unit_report)

        occ = int(self.driver.find_element_by_css_selector(
            "#tab_unitmix > table:nth-child(3) > tbody > tr:nth-child(1) > "
            "td:nth-child(2)").text.split(":")[1].replace("%", "")) / 100

        apo = {"property_id": _id,
               "date": datetime.date.today(),
               "occupancy": occ}

        apo_orm = AxioPropertyOccupancy(**apo)
        self.property_occupancy = apo_orm

        try:
            session.add(apo_orm)
            session.commit()
        except IntegrityError:
            session.rollback()
            session.flush()

        rc_list = []
        for unit in unit_report_list:
            rc = RentComp(**unit)
            rc_list.append(rc)
            if cache_res:
                try:
                    session.add(rc)
                    session.commit()
                except IntegrityError:
                    session.rollback()
                    session.flush()

        self.unit_mix = rc_list
        return 1


def run(prop_ids):
    axio = AxioScraper(headless=False)
    axio.mlg_axio_login()
    while 1:
        try:
            _id = prop_ids[0]
            axio.current_id = _id
            res = axio.navigate_to_property_report(_id)
            if res:
                res = axio.get_property_details(_id)
                if res:
                    axio.get_property_data(_id, cache_res=True)
                else:
                    traceback.print_exc()
                    print("Failed on {_id}".format(_id=_id))
                    return 0
            prop_ids.pop(0)
            r_int = random.uniform(0.01, 3)
            time.sleep(r_int)
        except:
            traceback.print_exc()
            return 0


def set_diff_discovery(floor=0):
    """

    """
    ids_found = AxioProperty.fetch_all_property_data()
    ids_found = [int(i.property_id) for i in ids_found]
    # generate key space
    k_space = list(range(1, 20000000))
    keys_to_search = list(set(k_space) - set(ids_found))
    keys_to_search.sort()
    keys_to_search = [i for i in keys_to_search if i > floor]
    run(keys_to_search)


def ascending_discovery():
    prop_ids = [i for i in range(1, 2000000)]
    run(prop_ids)


if __name__ == "__main__":
    floor = 69779
    set_diff_discovery(floor)
