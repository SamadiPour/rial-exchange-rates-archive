"""The codes the archive stores, with the names and the order its day files use.

The archive keeps its own copy instead of using the bonbast package's catalog. bonbast 2.0
changed the case of currency codes ("usd" became "USD") and some names, and the stored format
must not follow such changes. Day files before 2026-10-10 already use these names and this order.
"""

CURRENCIES: dict[str, str] = {
    "usd": "US Dollar",
    "eur": "Euro",
    "gbp": "British Pound",
    "chf": "Swiss Franc",
    "cad": "Canadian Dollar",
    "aud": "Australian Dollar",
    "sek": "Swedish Krona",
    "nok": "Norwegian Krone",
    "rub": "Russian Ruble",
    "thb": "Thai Baht",
    "sgd": "Singapore Dollar",
    "hkd": "Hong Kong Dollar",
    "azn": "Azerbaijani Manat",
    "amd": "10 Armenian Dram",
    "dkk": "Danish Krone",
    "aed": "UAE Dirham",
    "jpy": "10 Japanese Yen",
    "try": "Turkish Lira",
    "cny": "Chinese Yuan",
    "sar": "Saudi Riyal",
    "inr": "Indian Rupee",
    "myr": "Malaysian Ringgit",
    "afn": "Afghan Afghani",
    "kwd": "Kuwaiti Dinar",
    "iqd": "100 Iraqi Dinar",
    "bhd": "Bahraini Dinar",
    "omr": "Omani Rial",
    "qar": "Qatari Rial",
}

COINS: dict[str, str] = {
    "azadi1": "azadi",
    "emami1": "emami",
    "azadi1_2": "½ azadi",
    "azadi1_4": "¼ azadi",
    "azadi1g": "gerami",
}

NAMES: dict[str, str] = {**CURRENCIES, **COINS}

# The codes kept in the *_imp.min.json release files.
IMPORTANT: tuple[str, ...] = ("usd", "eur", "gbp")
