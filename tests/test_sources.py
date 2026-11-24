from fakes import RecordedHttp

from pipeline.sources.comtrade import ComtradeSource
from pipeline.sources.fx import FxSource
from pipeline.sources.pinksheet import PinkSheetSource
from pipeline.sources.tariffs import TariffSource
from pipeline.sources.wdi import WdiSource


def test_fx_source_reads_usd_rates_dated_by_the_feed_update():
    http = RecordedHttp(("https://open.er-api.com/v6/latest/USD", {}, "fx_open_er_api.json"))

    rows = FxSource().fetch(http).set_index("quote")

    assert rows.loc["KRW"].to_dict() == {"source": "fx", "date": "2026-11-24", "base": "USD", "rate": 1343.513843}
    assert rows.loc["VND", "rate"] == 25800.612967


def test_wdi_source_reads_one_row_per_country_indicator_year_with_units():
    http = RecordedHttp(("https://api.worldbank.org/v2/country/", {}, "wdi_gdp_pc.json"))

    rows = WdiSource(countries=["USA", "PHL"], indicators={"NY.GDP.PCAP.CD": "gdp_per_capita_usd"}).fetch(http)

    phl = rows.set_index(["iso3", "year"]).loc[("PHL", 2024)]
    assert phl.to_dict() == {
        "source": "wdi",
        "indicator": "gdp_per_capita_usd",
        "value": 3985.29464669706,
        "unit": "USD",
        "source_code": "NY.GDP.PCAP.CD",
        "imputed": False,
    }
    assert len(rows) == 6


def comtrade_http():
    preview = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
    return RecordedHttp(
        (preview, {"flowCode": "M"}, "comtrade_preview.json"),
        (preview, {"flowCode": "X"}, "comtrade_preview_kr_exports.json"),
    )


def test_comtrade_source_reads_partner_imports_from_world_and_korea():
    rows = ComtradeSource(countries=["PHL"], years=[2024], hs=["1704", "2105"]).fetch(comtrade_http())

    imports = rows[rows.flow == "M"].set_index(["partner_iso3", "hs"])
    assert imports.loc[("WLD", "1704"), ["reporter_iso3", "period", "value_usd", "net_kg"]].tolist() == [
        "PHL",
        "2024",
        134913420.0,
        93564663.89,
    ]
    assert imports.loc[("KOR", "2105"), "value_usd"] == 3718725.0


def test_comtrade_source_reads_korea_reported_exports_to_world_and_partners():
    rows = ComtradeSource(countries=["PHL"], years=[2024], hs=["1704", "2105"]).fetch(comtrade_http())

    exports = rows[rows.flow == "X"].set_index(["partner_iso3", "hs"])
    assert set(exports.reporter_iso3) == {"KOR"}
    assert exports.loc[("PHL", "1704"), "value_usd"] == 878436.0
    assert exports.loc[("WLD", "2105"), "value_usd"] == 98412620.0
    assert set(rows.freq) == {"A"} and set(rows.source) == {"comtrade"}


WITS = "https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN/reporter/"


def test_tariff_source_keeps_the_latest_mfn_year_per_product(tmp_path):
    http = RecordedHttp((WITS + "840/", {}, "wits_trn_usa.xml"))
    source = TariffSource(countries=["USA"], overrides_file=tmp_path / "none.yaml")

    rows = source.fetch(http).set_index("hs")

    assert rows.loc["170490", ["importer_iso3", "rate_type", "agreement", "effective_from", "rate_pct"]].tolist() == [
        "USA",
        "mfn",
        "",
        "2023-01-01",
        8.66250038146973,
    ]
    assert sorted(rows.index) == ["170410", "170490", "210500"]


def test_tariff_source_treats_no_records_as_no_rows(tmp_path):
    http = RecordedHttp((WITS, {}, "wits_no_records.txt"))

    rows = TariffSource(countries=["MMR"], overrides_file=tmp_path / "none.yaml").fetch(http)

    assert rows.empty


def test_tariff_source_adds_dated_overrides_from_the_override_file(tmp_path):
    overrides = tmp_path / "overrides.yaml"
    overrides.write_text("""
- importer_iso3: USA
  hs: ["1704", "1905"]
  rate_type: additional
  agreement: US reciprocal tariff
  rate_pct: 15
  effective_from: 2025-08-07
  source_url: https://ustr.gov
""")

    rows = TariffSource(countries=[], overrides_file=overrides).fetch(RecordedHttp())

    assert rows[["source", "importer_iso3", "hs", "rate_type", "rate_pct", "effective_from"]].values.tolist() == [
        ["override", "USA", "1704", "additional", 15.0, "2025-08-07"],
        ["override", "USA", "1905", "additional", 15.0, "2025-08-07"],
    ]


def test_pinksheet_source_finds_the_current_workbook_and_reads_monthly_prices():
    http = RecordedHttp(
        ("https://www.worldbank.org/en/research/commodity-markets", {}, "commodity_markets_page.html"),
        ("https://thedocs.worldbank.org/", {}, "pinksheet_monthly.xlsx"),
    )

    rows = PinkSheetSource().fetch(http).set_index(["commodity", "month"])

    assert rows.loc[("cocoa", "2026-10"), ["source", "price", "unit"]].tolist() == ["pinksheet", 5.75, "USD/kg"]
    assert rows.loc[("sugar_world", "2026-09"), "price"] == 0.41
    assert rows.loc[("wheat_us_hrw", "2026-08"), ["price", "unit"]].tolist() == [330.0, "USD/mt"]
    assert len(rows) == 12  # 4 commodities x 3 months
