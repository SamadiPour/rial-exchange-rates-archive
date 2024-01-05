import datetime
import json
import os

import jdatetime

artifact_dir = 'artifact'


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
    with open(os.path.join(artifact_dir, f'{base_directory}_all.json'), "w", encoding="utf8") as f:
        json.dump(aggregated_json, f, ensure_ascii=False)

    remove_nested_key(aggregated_json, 'name')
    with open(os.path.join(artifact_dir, f'{base_directory}_all.min.json'), "w", encoding="utf8") as f:
        json.dump(aggregated_json, f, separators=(",", ":"), ensure_ascii=False)

    for date, currencies in aggregated_json.items():
        for currency in list(currencies.keys()):
            if currency not in ['usd', 'eur', 'gbp']:
                currencies.pop(currency)
    with open(os.path.join(artifact_dir, f'{base_directory}_imp.min.json'), "w", encoding="utf8") as f:
        json.dump(aggregated_json, f, separators=(",", ":"), ensure_ascii=False)


walker('gregorian', datetime)
walker('jalali', jdatetime)
