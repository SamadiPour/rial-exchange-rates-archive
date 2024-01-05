import datetime
import json
import os

import jdatetime

artifact_dir = 'artifact'

currency_codes = ['usd', 'eur', 'gbp', 'chf', 'cad', 'aud', 'sek', 'nok', 'rub', 'thb', 'sgd', 'hkd', 'azn', 'amd',
                  'dkk',
                  'aed', 'jpy', 'try', 'cny', 'sar', 'inr', 'myr', 'afn', 'kwd', 'iqd', 'bhd', 'omr', 'qar', 'azadi1',
                  'emami1', 'azadi1_2', 'azadi1_4', 'azadi1g']


def remove_nested_key(data, key):
    if isinstance(data, dict):
        for k in list(data.keys()):
            if k == key:
                del data[k]
            else:
                remove_nested_key(data[k], key)
    elif isinstance(data, list):
        for item in data:
            remove_nested_key(item, key)


def aggregator(files: iter) -> dict:
    date_json_map = dict()
    for file_path in files:
        date_str = '/'.join(file_path.split('/')[1:])
        with open(file_path, encoding="utf8") as f:
            data = json.load(f)
        date_json_map[date_str] = data
    return date_json_map


def write_json(path: str, data: dict, remove_spaces: bool):
    with open(path, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":") if remove_spaces else None)


def walker(base_directory: str, dt):
    file_list = []
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
        path = os.path.join(base_directory, year)
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
    os.makedirs(artifact_dir, exist_ok=True)
    os.makedirs(os.path.join(artifact_dir, 'currency'), exist_ok=True)

    # output the full file without any changes
    write_json(os.path.join(artifact_dir, f'{base_directory}_all.json'), aggregated_json, remove_spaces=False)

    # output for everything but in a compressed way
    remove_nested_key(aggregated_json, 'name')
    write_json(os.path.join(artifact_dir, f'{base_directory}_all.min.json'), aggregated_json, remove_spaces=True)

    # create file for each currency
    for currency in currency_codes:
        currency_data = {}
        for date, data in aggregated_json.items():
            if currency in data:
                currency_data[date] = data[currency]
        write_json(os.path.join(artifact_dir, 'currency', f'{currency}.json'), currency_data, remove_spaces=True)

    # output for impt currencies (usd-eur-gbp)
    imp_data = {}
    for date, data in aggregated_json.items():
        imp_data[date] = {key: value for key, value in data.items() if key in ['usd', 'eur', 'gbp']}
    write_json(os.path.join(artifact_dir, f'{base_directory}_imp.min.json'), imp_data, remove_spaces=True)


walker('gregorian', datetime)
walker('jalali', jdatetime)
