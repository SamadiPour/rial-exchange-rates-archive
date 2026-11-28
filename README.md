# Rial Exchange Rates Archive

This repository serves as the archive for Iranian Rial (IRR) currency conversion rates sourced
from [bonbast.com](https://bonbast.com/). The exchange rates are automatically updated every day using a GitHub Actions
workflow.

The primary goal of this repository is to maintain a comprehensive historical record of Iranian Rial exchange rates over
time.

Please note that all prices in this repository are in `Toman`.

## Table of Contents

- [Structure](#structure)
    * [`{year}/{month}/{day}` file model](#yearmonthday-file-model)
    * [`full` file model](#full-file-model)
- [Files](#files)
- [Usage](#usage)
    * [Getting exchange rates for specific date](#getting-exchange-rates-for-specific-date)
    * [Converting `full` file to date-price map/dict](#converting-full-file-to-date-price-mapdict)
    * [Converting `full` files to array/list](#converting-full-files-to-arraylist)
- [Currencies](#currencies)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Structure

The repository is organized into two main directories: `gregorian` and `jalali`. Both directories have the same format
and type of files, with the only difference being the date.

```text
├── gregorian
│   └── {year}
│       ├── full -> contain every day in that year
│       └── {month}
│           ├── full -> contain every day in that month
│           └── {day}
├── jalali
│   └── {year}
│       ├── full -> contain every day in that year
│       └── {month}
│           ├── full -> contain every day in that month
│           └── {day}
├── rates_archive -> the scripts that update the archive (see Development)
└── tests
```

### `{year}/{month}/{day}` file model

These files contain the daily currency conversion rates. They all have the same DTO for convenience.

> Please note that the starting file is always 2012/10/09 for gregorian and 1391/07/18 for jalali.

```text
{
  "{currency-code}": {
    "name": <string>,
    "sell": <int>,
    "buy": <int>
  }
}
```

Currency codes are always lowercase (`usd`, `azadi1`); see [Currencies](#currencies). On the few days bonbast has no buy
price for a currency, `buy` is left out.

### `full` file model

Every year and month directory has a `full` file that contains every day in it (so far, for the current year and month)
with the same DTO structure.

```text
{
  "{date}": {
    "{currency-code}": {
      "name": <string>,
      "sell": <int>,
      "buy": <int>
    }
  }
}
```

## Files

Every night, automated scripts generate the following types of release files:

- `{calendar}_all.json`: Contains all the information from the start
- `{calendar}_all.min.json`: Similar to the previous one, but whitespaces and the `name` field (from currency DTO) is
  removed
- `{calendar}_imp.min.json`: Similar to the previous one, but only for USD, EUR, and GBP
- `{calendar}_31days.min.json`: Contains all currencies in the past 31 days
- `{calendar}_7days.min.json`: Contains all currencies in the past 7 days

`{calendar}` is `gregorian` or `jalali`.

> Note: Only the last 10 releases are retained. That means you always have to a get the last one like this:
> ```bash
> curl -Ls https://github.com/SamadiPour/rial-exchange-rates-archive/releases/latest/download/gregorian_imp.min.json | jq
> ```

### `data` branch files

This repository also includes an orphan branch that contains generated outputs. The branch will always have just one
commit and no history. The data stored in this branch is identical to the release section, but it also includes the
following files:

- `/currency/{currency-code}.json`: Contains currency specific information from the start, keyed by Jalali dates

> CORS Issue: If you are encountering CORS error while getting the release files, you can instead use the files stored
> in the `data` branch. For example, try one of these two links:
> ```text
> - https://raw.githubusercontent.com/SamadiPour/rial-exchange-rates-archive/data/gregorian_imp.min.json
> - https://cdn.jsdelivr.net/gh/SamadiPour/rial-exchange-rates-archive@data/gregorian_imp.min.json
> ```

## Usage

You can access the historical exchange rate data by exploring the contents of this repository. The data is organized and
stored in a structured format, allowing for easy retrieval and analysis.

### Getting exchange rates for specific date

The output of these examples will be like this:

```json
{
  "usd": {
    "name": "US Dollar",
    "sell": 3400,
    "buy": 3300
  }
}
```

```bash
# == Bash + jq ==
curl -s https://raw.githubusercontent.com/SamadiPour/rial-exchange-rates-archive/main/gregorian/2015/10/15
```

```python
# == Python ==
import requests
import json

response = requests.get(
    'https://raw.githubusercontent.com/SamadiPour/rial-exchange-rates-archive/main/gregorian/2015/05/10'
)
response.raise_for_status()
prices = json.loads(response.text)
print(prices)
print(prices.get('usd', {}).get('buy', None))
```

```js
// JavaScript
fetch('https://raw.githubusercontent.com/SamadiPour/rial-exchange-rates-archive/main/jalali/1395/05/01')
    .then(response => response.json())
    .then(data => {
        console.log(data);
        console.log(data.usd.buy);
    })
    .catch(error => {
        console.error('Error:', error)
    })
```

### Converting `full` file to date-price map/dict

The output of these examples will be like this:

```json
{
  "2013/01/01": 3205,
  "2013/01/02": 3190,
  "2013/01/03": 3195
}
```

Examples:

```bash
# == Bash + jq ==
curl -s https://raw.githubusercontent.com/SamadiPour/rial-exchange-rates-archive/main/gregorian/2015/10/full | jq 'to_entries | map({key: .key, value: .value.usd.buy}) | from_entries'
```

```python
# == Python ==
import requests
import json

response = requests.get(
    'https://raw.githubusercontent.com/SamadiPour/rial-exchange-rates-archive/main/gregorian/2015/full'
)
response.raise_for_status()
data = json.loads(response.text)
prices = {key: value['eur']['buy'] for key, value in data.items()}
print(prices)
```

```js
// JavaScript
fetch('https://raw.githubusercontent.com/SamadiPour/rial-exchange-rates-archive/main/jalali/1395/05/full')
    .then(response => response.json())
    .then(data => {
        const prices = Object.fromEntries(
            Object.entries(data).map(([key, value]) => [key, value.usd.sell])
        );
        console.log(prices);
    })
    .catch(error => {
        console.error('Error:', error)
    })
```

### Converting `full` files to array/list

The output of these examples will be like this:

```json
[
  3205,
  3190,
  3195
]
```

Examples:

```bash
# == Bash + jq ==
curl -s https://raw.githubusercontent.com/SamadiPour/rial-exchange-rates-archive/main/gregorian/2015/10/full | jq '[.[] | .usd.buy]'
```

```python
# == Python ==
import requests
import json

response = requests.get(
    'https://raw.githubusercontent.com/SamadiPour/rial-exchange-rates-archive/main/gregorian/2015/full'
)
response.raise_for_status()
data = json.loads(response.text)
prices = (value["eur"]["buy"] for value in data.values())
print(prices)
```

```js
// JavaScript
fetch('https://raw.githubusercontent.com/SamadiPour/rial-exchange-rates-archive/main/jalali/1395/05/full')
    .then(response => response.json())
    .then(data => {
        const prices = Object.values(data).map(item => item.usd.sell);
        console.log(prices);
    })
    .catch(error => {
        console.error('Error:', error)
    })
```

# Currencies

| Flag | Currency          | Code |
|:----:|-------------------|:----:|
| 🇺🇸 | US Dollar         | USD  |
| 🇪🇺 | Euro              | EUR  |
| 🇬🇧 | British Pound     | GBP  |
| 🇨🇭 | Swiss Franc       | CHF  |
| 🇨🇦 | Canadian Dollar   | CAD  |
| 🇦🇺 | Australian Dollar | AUD  |
| 🇸🇪 | Swedish Krona     | SEK  |
| 🇳🇴 | Norwegian Krone   | NOK  |
| 🇷🇺 | Russian Ruble     | RUB  |
| 🇹🇭 | Thai Baht         | THB  |
| 🇸🇬 | Singapore Dollar  | SGD  |
| 🇭🇰 | Hong Kong Dollar  | HKD  |
| 🇦🇿 | Azerbaijani Manat | AZN  |
| 🇦🇲 | 10 Armenian Dram  | AMD  |
| 🇩🇰 | Danish Krone      | DKK  |
| 🇦🇪 | UAE Dirham        | AED  |
| 🇯🇵 | 10 Japanese Yen   | JPY  |
| 🇹🇷 | Turkish Lira      | TRY  |
| 🇨🇳 | Chinese Yuan      | CNY  |
| 🇸🇦 | Saudi Riyal       | SAR  |
| 🇮🇳 | Indian Rupee      | INR  |
| 🇲🇾 | Malaysian Ringgit | MYR  |
| 🇦🇫 | Afghan Afghani    | AFN  |
| 🇰🇼 | Kuwaiti Dinar     | KWD  |
| 🇮🇶 | 100 Iraqi Dinar   | IQD  |
| 🇧🇭 | Bahraini Dinar    | BHD  |
| 🇴🇲 | Omani Rial        | OMR  |
| 🇶🇦 | Qatari Rial       | QAR  |

| Coins   | Code     |
|---------|----------|
| Azadi   | azadi1   |
| Emami   | emami1   |
| ½ Azadi | azadi1_2 |
| ¼ Azadi | azadi1_4 |
| Gerami  | azadi1g  |

## Development

The [daily workflow](.github/workflows/daily_update.yml) runs the `rates_archive` package. It needs
[uv](https://docs.astral.sh/uv/):

```bash
uv sync
uv run python -m rates_archive fetch       # fetch every missing day up to yesterday (Tehran time)
uv run python -m rates_archive aggregate   # rebuild the `full` files
uv run python -m rates_archive verify      # check for gaps, format drift and gregorian/jalali mismatches
uv run python -m rates_archive artifacts   # write the release files to artifact/
uv run pytest
```

`fetch` starts from the day after the newest stored day, so a missed run is caught up by the next one. It stores every
day under both calendars, in the format above, whatever format the `bonbast` package returns. If a day cannot be
fetched it stops there, so the archive never has a gap. Run `python -m rates_archive fetch --help` for its options.

If `verify` reports files that are not in the archive's format, `python -m rates_archive normalize` rewrites them.

## Contributing

Contributions to this repository are welcome! If you notice any issues, discrepancies, or have suggestions for
improvement, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. Feel free to use the data and code in accordance with the terms
specified in the license.

> Disclaimer: The exchange rates provided in this repository are sourced from bonbast.com, and any discrepancies or
> inaccuracies in the data are beyond the control of the repository maintainers.