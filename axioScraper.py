from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
import requests
import json
from datetime import date
import datetime
from selenium import webdriver
import os
import sys
import time
import traceback
import usaddress
import random

packages_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
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
        self.property_report_transactions = 'https://axio.realpage.com/PropertyReport/Transactions/'
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
            time.sleep(2)
            # Pass off cookies to Session handler:
            self.cookies = self.driver.get_cookies()
            self.headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
            }

            self.session = requests.session()
            for cookie in self.cookies:
                self.session.cookies.set(cookie['name'], cookie['value'])
            self.driver.quit()
            return 1
        except:
            return 0

    def mlg_axio_login(self):
        with open(os.path.join(self.curr_dir, "pwd.json")) as json_file:
            data = json.load(json_file)
            mlg_username = data["axio_login"]["username"]
            mlg_password = data["axio_login"]["password"]
        return self.login(mlg_username, mlg_password, self.login_path)

    def get_property_report(self, _id):
        """
        "NAVIGATE TO PROPERTY PAGE, CHECKS IF ID IS VALID, RETURN SOUP"
        :param _id:
        :return:
        """
        url = os.path.join(self.property_report_path, str(_id))
        r_count = 0
        while 1:
            req = self.session.get(url)
            if self.session.get(url).status_code == 200:
                soup = BeautifulSoup(req.text, 'html.parser')
                if soup.select_one('h1') is not None and 'error' in soup.select_one('h1').text.lower():
                    print("Error Page Not Found for {_id}".format(_id=_id))
                    return 0
                if soup.find('span', {'id': 'property-name'}) is not None:
                    self.property_res = req
                    self.property_soup = soup
                    return 1
            else:
                if r_count > 2:
                    return 0
                r_count += 1

    def get_property_details(self, _id):
        """
        must call navigate_to_property_report prior to call
        :return:
        """

        _id = str(_id)
        records = []
        try:
            records = session.query(AxioProperty).filter(AxioProperty.property_id == _id).one()
            print("Axio Property already Indexed!")
        except NoResultFound:
            print("Axio Property {_id} not in Database - Adding!".format(_id=_id))

        try:
            if not records:
                soup = self.property_soup
                property_details = dict()
                property_details["property_id"] = _id
                property_details["property_address"] = soup.find('h2').find('small').text
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

                # done
                try:
                    property_details["property_name"] = soup.select_one('#property-name').text.strip()
                except NoSuchElementException:
                    property_details["property_name"] = None

                # done
                try:
                    k = [k for k, v in enumerate(soup.find_all('dt')) if v.text == "True Owner:"][0]
                    prop_owner = soup.find_all('dd')[k].text.strip()
                    property_details["property_owner"] = prop_owner
                except:
                    property_details["property_owner"] = None

                # done
                try:
                    k = [k for k, v in enumerate(soup.find_all('dt')) if v.text == "Manager:"][0]
                    manager = soup.find_all('dd')[k].text.strip()
                    property_details["property_management"] = manager
                except:
                    property_details["property_management"] = None

                # done
                try:
                    year_built = int(soup.select_one(
                        '#tab_unitmix > table:nth-child(3) > tbody > tr:nth-child(1) > td:nth-child(4)').text.split(
                        ':')[1])
                    property_details["year_built"] = year_built
                except:
                    property_details["year_built"] = None

                # done
                try:
                    property_details["total_units"] = int(soup.select_one(
                        '#tab_unitmix > table:nth-child(3) > tbody > tr:nth-child(1) > td:nth-child(1)').text.split(
                        ':')[1].replace(',', ""))
                except:
                    property_details["total_units"] = None

                # done
                try:
                    k = [k for k, v in enumerate(soup.find_all('dt')) if v.text == "Website:"][0]
                    website = soup.find_all('dd')[k].find('a', href=True)['href']
                    property_details["property_website"] = website
                except:
                    property_details["property_website"] = None

                # done
                try:
                    asset_grade_market = soup.select_one('#body-container > div > div.col-md-2 > div > a:nth-child(5) > p:nth-child(2)').text
                    property_details["property_asset_grade_market"] = asset_grade_market
                except:
                    property_details["property_asset_grade_market"] = None

                # done
                try:
                    asset_grade_submarket = soup.select_one('#body-container > div > div.col-md-2 > div > a:nth-child(6) > p:nth-child(2)').text
                    property_details["property_asset_grade_submarket"] = asset_grade_submarket
                except:
                    property_details["property_asset_grade_submarket"] = None

                # done
                try:
                    msa = soup.select_one('#body-container > div > div.col-md-2 > div > a:nth-child(2) > p:nth-child(2)').text
                    property_details["msa"] = msa
                except:
                    property_details["msa"] = None

                # done
                try:
                    submarket_name = soup.select_one('#body-container > div > div.col-md-2 > div > a:nth-child(3) > p:nth-child(2)').text
                    property_details["submarket_name"] = submarket_name
                except:
                    property_details["submarket_name"] = None

                # done
                try:
                    survey = soup.select_one('#body-container > div > div.col-md-2 > div > a:nth-child(7) > p:nth-child(2)').text
                    property_details["survey_date"] = survey
                except:
                    property_details["survey_date"] = None

                try:
                    unit_mix = self.get_unit_mix_helper(_id, soup)
                    square_feet = sum([float(i['area'])*int(i['quantity']) for i in unit_mix])
                    property_details["total_square_feet"] = square_feet
                except:
                    property_details["total_square_feet"] = None

                # todo: add error checking
                prop_trans_path = self.property_report_transactions + _id
                trans_res = self.session.get(prop_trans_path)
                prop_trans_soup = BeautifulSoup(trans_res.text)

                # done
                try:
                    status = prop_trans_soup.select_one(
                        'body > div.container-fluid > div:nth-child(4) > div > table > tbody > tr:nth-child(1) > '
                        'td:nth-child(2)').text.split(':')[1].strip()
                    property_details["status"] = status
                except:
                    property_details["status"] = None

                # done
                try:
                    lsd = prop_trans_soup.select_one(
                        'body > div.container-fluid > div:nth-child(2) > div > table > tbody > tr:nth-child(1) > td:nth-child(2)').text.split(
                        ':')[1].strip()
                    property_details["last_sale_date"] = lsd
                    if property_details["last_sale_date"] == "":
                        property_details["last_sale_date"] = None
                except NoSuchElementException:
                    property_details["last_sale_date"] = None

                # done
                try:
                    lsp = prop_trans_soup.select_one(
                        'body > div.container-fluid > div:nth-child(2) > div > table > tbody > tr:nth-child(4) > td:nth-child(1)').text.split(
                        ":")[1].strip()
                    property_details["last_sale_price"] = lsp
                except:
                    property_details["last_sale_price"] = None

                # done
                try:
                    ppn = prop_trans_soup.select_one(
                        'body > div.container-fluid > div:nth-child(2) > div > table > tbody > '
                        'tr:nth-child(3) > td:nth-child(3)').text.split(":")[1].strip()
                    property_details["parcel_number"] = ppn
                except:
                    property_details["parcel_number"] = None

                # done
                try:
                    levels = int(prop_trans_soup.select_one(
                        'body > div.container-fluid > div:nth-child(4) > div > table > tbody >'
                        ' tr:nth-child(1) > td:nth-child(3)').text.split(":")[1])
                    property_details["levels"] = levels
                except:
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
                self.property_details = records

        except Exception:
            print("FAILED ON PROPERTY ID {ID}".format(ID=_id))
            traceback.print_exc()
            return 0

        return 1

    def get_unit_mix_helper(self, _id, soup):

        try:
            tbl = soup.select('#tab_unitmix > table:nth-child(5) > tbody')[0].find_all('tr')[2:]
        except NoSuchElementException:
            tbl = []

        unit_report_list = []
        for j, row in enumerate(tbl):
            stripped_row = [i.text.strip() for i in row.find_all('td')]
            tbl_width = len(stripped_row)
            if tbl_width >= 7:
                d_tbl = stripped_row
                if bool(d_tbl):
                    unit_report = dict()
                    unit_report["property_id"] = _id
                    unit_report["date_added"] = str(date.today())
                    unit_report["unit_mix_id"] = j + 1
                    for i, cell in enumerate(d_tbl):
                        if i == 0:
                            unit_report["type"] = cell.replace("/", "B/")
                        elif i == 1:
                            unit_report["area"] = cell.replace(",", "")

                        elif i == 2:
                            unit_report["quantity"] = cell.replace(",", "")

                        elif i == 5:
                            unit_report["avg_market_rent"] = cell.replace("$", "").replace(",", "")
                        elif i == 9:
                            unit_report["avg_effective_rent"] = cell.replace("$", "").replace(",", "")

                    if bool(unit_report):
                        unit_report_list.append(unit_report)

        return unit_report_list

    def get_property_data(self, _id, cache_res=True):
        """
        must call navigate_to_property_report prior to call
        :param _id:
        :param cache_res:
        :param return_res:
        :return:
        """
        _id = str(_id)
        soup = self.property_soup
        unit_report_list = self.get_unit_mix_helper(_id, soup)

        occ = float(soup.select_one(
            '#tab_unitmix > table:nth-child(3) > tbody > tr:nth-child(1) > td:nth-child(2)').text.split(
            ':')[1].replace('%', "")) / 100

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


def run(prop_ids):
    axio = AxioScraper(headless=True)
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
