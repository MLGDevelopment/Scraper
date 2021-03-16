import requests
import os
import pandas as pd

curr_dir = os.path.dirname(os.path.realpath(__file__))
permit_data_path = os.path.join(curr_dir, "data", "permits")



def eol(line_item):
    parsed_line = []
    first_two = line_item[:2]
    first_two = [i.strip() for i in first_two]
    del line_item[0], line_item[0]
    parsed_line = parsed_line + first_two
    dps = line_item[-7:]
    dps = [i.strip() for i in dps]
    parsed_line = parsed_line + dps
    line_item = line_item[:-7]
    city = ''
    state = ''
    for i, val in enumerate(line_item):
        if len(val.split(",")) == 1:
            city = city + " " + val
        else:
            city = city + " " + val
            state = line_item[i + 1]
            break
    parsed_line.append(city.strip())
    parsed_line.append(state.strip())
    return parsed_line

def parse_text(data, path):
    # cb_permits_mtd_data.split("\n\n")[1].split("\n")[0].split(" ")

    split_headers = data.split("\n\n")

    split_osd = data.split(" ")
    start_index = 0
    permit_data = []
    while 1:
        try:
            if "percent" in split_osd[start_index].lower():
                find_start = split_osd[start_index].split("\n")
                if len(find_start) > 1:
                    index = 0
                    while 1:
                        try:
                            int(find_start[index])
                            break
                        except ValueError or TypeError:
                            index = index + 1


                    permit_data = split_osd[start_index + 1:]
                    permit_data.insert(0, find_start[index])
                break
            else:
                start_index = start_index + 1
        except:
            pass

    # permit_data = split_headers[1]
    split_data = permit_data

    master_data = []
    line_item = []
    count = 0
    was_city_found = False
    new_line_hit = False

    # start
    for i, data_point in enumerate(split_data):
        dp_len = len(data_point)

        if len(master_data) == 12:
            print

        is_city = data_point.split(",")
        if len(is_city) == 2:
            is_city = True
        else:
            is_city = False

        # test for new line--doesnt mean we have new line item
        nl_present = data_point.split("\n")
        if len(nl_present) == 2:
            if count != 7:
                # we dont have a new line item
                line_item.append(nl_present[0])
                line_item.append(nl_present[1])
                # count = count + 1
            else:
                # we have a new line item
                was_city_found = False
                line_item.append(nl_present[0])
                line_item = eol(line_item)
                master_data.append(line_item)
                line_item = []
                line_item.append(nl_present[1])
                count = 0
                continue

        # base case for first two columns
        if count != 8:
            if data_point == '':
                continue
            elif data_point != '' and not is_city and not was_city_found:
                line_item.append(data_point)
            elif is_city:
                # ciy was found, increment
                line_item.append(data_point)
                was_city_found = True
            elif data_point != '':
                # append all other data
                line_item.append(data_point)
                count = count + 1
        else:
            was_city_found = False
            count = 0
            line_item = eol(line_item)
            master_data.append(line_item)
            line_item = []


    if len(master_data) > 0:
        del master_data[-1]
        return master_data
    else:
        return []




def pull_and_save_text():
    years = list(range(2010, 2014))
    years.reverse()
    months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
    month_code = 'tb3u'
    ytd_code = 't3yu'
    month_year_comb = {}
    for year in years:
        for month in months:

            cb_permits_mtd = "https://www.census.gov/construction/bps/txt/{code}{year}{month}.txt".format(code=month_code,
                                                                                                          year=year,
                                                                                                          month=month)

            cb_permits_mtd_data = requests.get(cb_permits_mtd).text
            parse_text(cb_permits_mtd_data)
            f_name = "{year}{month}-mtd.txt".format(year=year, month=month)
            mtd_output = os.path.join(permit_data_path, f_name)
            with open(mtd_output, "w") as text_file:
                text_file.write(cb_permits_mtd_data)

            cb_permits_ytd = "https://www.census.gov/construction/bps/txt/{code}{year}{month}.txt".format(code=ytd_code,
                                                                                                          year=year,
                                                                                                          month=month)

            cb_permits_ytd_data = requests.get(cb_permits_ytd).text
            f_name = "{year}{month}-ytd.txt".format(year=year, month=month)
            ytd_output = os.path.join(permit_data_path, f_name)
            with open(ytd_output, "w") as text_file:
                text_file.write(cb_permits_ytd_data)


def pull_and_parse():
    years = list(range(2019, 2020))
    #years.reverse()
    months = ['01', '02', '03', '05', '06', '07', '08', '09', '10' ]
    #
    month_code = 'tb3u'
    ytd_code = 't3yu'

    month_year_comb = {}
    for year in years:
        for month in months:

            _id = "{YEAR}-{MONTH}".format(YEAR=year, MONTH=month)

            cb_permits_mtd = "https://www.census.gov/construction/bps/txt/{code}{year}{month}.txt".format(
                code=month_code,
                year=year,
                month=month)

            cb_permits_mtd_data = requests.get(cb_permits_mtd).text
            mtd_data_parsed = parse_text(cb_permits_mtd_data, cb_permits_mtd)

            cb_permits_ytd = "https://www.census.gov/construction/bps/txt/{code}{year}{month}.txt".format(code=ytd_code,
                                                                                                          year=year,
                                                                                                          month=month)

            if len(mtd_data_parsed) != 0:
                month_year_comb[_id] = mtd_data_parsed

            cb_permits_ytd_data = requests.get(cb_permits_ytd).text
            # ytd_data_parsed = parse_text(cb_permits_ytd_data)
            print

    master_df = pd.DataFrame()
    for key in month_year_comb.keys():
        df = pd.DataFrame(month_year_comb[key])
        df["period"] = key
        master_df = master_df.append(df)
    print
    master_df.to_excel("combined_permit_data2.xlsx")

if __name__ == "__main__":
    pull_and_parse()