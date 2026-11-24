"""Screening scope shared by the pipeline and the analysis (see docs/pm/03_data_analysis.md §1)."""

# ISO3 -> (UN M49 code used by Comtrade and WITS, name)
CANDIDATES: dict[str, tuple[int, str]] = {
    "USA": (842, "United States"),
    "CAN": (124, "Canada"),
    "MEX": (484, "Mexico"),
    "BRA": (76, "Brazil"),
    "GBR": (826, "United Kingdom"),
    "DEU": (276, "Germany"),
    "FRA": (251, "France"),
    "NLD": (528, "Netherlands"),
    "POL": (616, "Poland"),
    "CHN": (156, "China"),
    "JPN": (392, "Japan"),
    "TWN": (490, "Taiwan"),
    "HKG": (344, "Hong Kong"),
    "MNG": (496, "Mongolia"),
    "VNM": (704, "Vietnam"),
    "THA": (764, "Thailand"),
    "IDN": (360, "Indonesia"),
    "PHL": (608, "Philippines"),
    "MYS": (458, "Malaysia"),
    "SGP": (702, "Singapore"),
    "KHM": (116, "Cambodia"),
    "MMR": (104, "Myanmar"),
    "IND": (699, "India"),
    "PAK": (586, "Pakistan"),
    "KAZ": (398, "Kazakhstan"),
    "AUS": (36, "Australia"),
    "NZL": (554, "New Zealand"),
    "ARE": (784, "United Arab Emirates"),
    "SAU": (682, "Saudi Arabia"),
    "RUS": (643, "Russia"),
}
ISO2 = {  # 관세청 (data.go.kr) uses ISO 3166 alpha-2 country codes
    "USA": "US",
    "CAN": "CA",
    "MEX": "MX",
    "BRA": "BR",
    "GBR": "GB",
    "DEU": "DE",
    "FRA": "FR",
    "NLD": "NL",
    "POL": "PL",
    "CHN": "CN",
    "JPN": "JP",
    "TWN": "TW",
    "HKG": "HK",
    "MNG": "MN",
    "VNM": "VN",
    "THA": "TH",
    "IDN": "ID",
    "PHL": "PH",
    "MYS": "MY",
    "SGP": "SG",
    "KHM": "KH",
    "MMR": "MM",
    "IND": "IN",
    "PAK": "PK",
    "KAZ": "KZ",
    "AUS": "AU",
    "NZL": "NZ",
    "ARE": "AE",
    "SAU": "SA",
    "RUS": "RU",
}

# WITS uses ISO 3166 numeric codes; these differ from Comtrade's M49 codes above
WITS_CODE_OVERRIDES = {"USA": 840, "FRA": 250, "IND": 356, "TWN": 158}


def wits_code(iso3: str) -> int:
    return WITS_CODE_OVERRIDES.get(iso3, CANDIDATES[iso3][0])


HS = ["1704", "1806", "1905", "2105"]
HS6 = {  # 6-digit lines under each HS4 heading, for tariff lookups (WITS has no HS4 rates)
    "1704": ["170410", "170490"],
    "1806": ["180610", "180620", "180631", "180632", "180690"],
    "1905": ["190510", "190520", "190531", "190532", "190540", "190590"],
    "2105": ["210500"],
}
KOREA_M49 = 410
HUBS = {"HKG", "SGP", "NLD", "ARE"}  # re-export hubs: imports overstate local consumption
SANCTIONED = {"RUS"}
NOT_IN_WORLD_BANK = {"TWN"}  # Taiwan is not a Comtrade reporter and not in WDI

# WDI code -> (indicator name, unit)
WDI: dict[str, tuple[str, str]] = {
    "NY.GDP.PCAP.CD": ("gdp_per_capita_usd", "USD"),
    "NY.GDP.MKTP.KD.ZG": ("gdp_growth_pct", "%"),
    "SP.POP.TOTL": ("population", "persons"),
    "SP.URB.TOTL.IN.ZS": ("urban_pct", "%"),
    "SP.POP.1564.TO.ZS": ("pop_15_64_pct", "%"),
    "SP.POP.0014.TO.ZS": ("pop_0_14_pct", "%"),
    "NE.CON.PRVT.PC.KD": ("hh_consumption_pc_const_usd", "constant 2015 USD"),
    "FP.CPI.TOTL.ZG": ("inflation_pct", "%"),
    "LP.LPI.OVRL.XQ": ("lpi_score", "score 1-5"),
}
