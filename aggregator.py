import datetime
import json
import os

import jdatetime


# currencies = ['usd', 'eur', 'gbp', 'chf', 'cad', 'aud', 'sek', 'nok', 'rub', 'thb', 'sgd', 'hkd', 'azn', 'amd', 'dkk',
#               'aed', 'jpy', 'try', 'cny', 'sar', 'inr', 'myr', 'afn', 'kwd', 'iqd', 'bhd', 'omr', 'qar', 'emami1',
#               'azadi1g', 'azadi1', 'azadi1_2', 'azadi1_4']


def aggregator(files: iter) -> dict:
    date_json_map = dict()
    for file_path in files:
        date_str = '/'.join(file_path.split('/')[1:])
        with open(file_path) as f:
            data = json.load(f)
        date_json_map[date_str] = data
    return date_json_map


def walker(base_directory: str, dt):
    year_directories = sorted(
        [
            d for d in os.listdir(os.path.join(base_directory))
            if os.path.isdir(os.path.join(base_directory, d)) and d.isdigit()
        ],
    )
    for year in year_directories:
        month_directories = sorted(
            [
                d for d in os.listdir(os.path.join(base_directory, year))
                if os.path.isdir(os.path.join(base_directory, year, d)) and d.isdigit()
            ],
        )
        # monthly
        for month in month_directories:
            path = os.path.join(base_directory, year, month)
            if os.path.exists(os.path.join(path, 'full')):
                continue

            date = dt.datetime.strptime(f'{year}/{month}', '%Y/%m')
            last_date_in_month = date.replace(
                year=date.year + 1 if date.month == 12 else date.year,
                month=1 if date.month == 12 else date.month + 1,
                day=1
            ) - dt.timedelta(days=1)
            if os.path.exists(os.path.join(path, last_date_in_month.strftime('%d'))):
                aggregated_json = aggregator(
                    sorted(
                        [
                            os.path.join(path, f) for f in os.listdir(path)
                            if os.path.isfile(os.path.join(path, f)) and f.isdigit()
                        ],
                    )
                )
                with open(os.path.join(path, 'full'), "w") as f:
                    json.dump(aggregated_json, f)

        # yearly
        path = os.path.join(base_directory, year)
        if os.path.exists(os.path.join(path, 'full')):
            continue

        date = dt.datetime.strptime(f'{year}', '%Y')
        last_date_in_year = date.replace(year=date.year + 1, month=1, day=1) - dt.timedelta(days=1)
        file_list = []
        if os.path.exists(os.path.join(path, last_date_in_year.strftime('%m'), last_date_in_year.strftime('%d'))):
            for month in month_directories:
                file_list.extend(
                    sorted(
                        [
                            os.path.join(path, month, f) for f in os.listdir(os.path.join(path, month))
                            if os.path.isfile(os.path.join(path, month, f)) and f.isdigit()
                        ],
                    )
                )
            aggregated_json = aggregator(file_list)
            with open(os.path.join(path, 'full'), "w") as f:
                json.dump(aggregated_json, f)


walker('gregorian', datetime)
walker('jalali', jdatetime)
