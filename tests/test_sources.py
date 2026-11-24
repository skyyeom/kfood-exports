import openpyxl
import pytest
from fakes import FIXTURES, RecordedHttp

from pipeline.config import CANDIDATES
from pipeline.sources.comtrade import ComtradeSource
from pipeline.sources.fx import FxSource
from pipeline.sources.kcs_monthly import KcsItemsSource, KcsMonthlySource, KcsNationsSource
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


def pinksheet_http():
    return RecordedHttp(
        ("https://www.worldbank.org/en/research/commodity-markets", {}, "commodity_markets_page.html"),
        ("https://thedocs.worldbank.org/", {}, "pinksheet_monthly.xlsx"),
    )


def test_pinksheet_source_reads_prices_from_the_workbook_linked_on_the_page():
    rows = PinkSheetSource().fetch(pinksheet_http()).set_index(["commodity", "month"])

    assert rows.loc[("cocoa", "2026-10"), ["source", "price", "unit"]].tolist() == ["pinksheet", 5.75, "USD/kg"]


def test_pinksheet_source_reads_every_month_for_each_commodity_with_its_unit():
    rows = PinkSheetSource().fetch(pinksheet_http())

    assert rows.groupby("commodity").month.nunique().to_dict() == {
        "cocoa": 3,
        "palm_oil": 3,
        "sugar_world": 3,
        "wheat_us_hrw": 3,
    }
    assert rows.set_index(["commodity", "month"]).loc[("wheat_us_hrw", "2026-08"), "unit"] == "USD/mt"


def test_wdi_source_reports_the_api_error_message(tmp_path):
    (tmp_path / "err.json").write_text('[{"message": [{"id": "120", "key": "Invalid value", "value": "bad"}]}]')
    http = RecordedHttp(("https://api.worldbank.org/", {}, str(tmp_path / "err.json")))

    with pytest.raises(RuntimeError, match="Invalid value"):
        WdiSource(countries=["USA"], indicators={"NY.GDP.PCAP.CD": "gdp_per_capita_usd"}).fetch(http)


def test_pinksheet_source_tolerates_blank_unit_cells_and_padded_names(tmp_path):
    wb = openpyxl.load_workbook(FIXTURES / "pinksheet_monthly.xlsx")
    ws = wb["Monthly Prices"]
    header = next(r for r in ws.iter_rows() if any(c.value == "Cocoa" for c in r))
    for cell in header:
        if cell.value == "Cocoa":
            cell.value = "Cocoa "
        elif cell.value and cell.value not in ("Sugar, world", "Wheat, US HRW", "Palm oil"):
            ws.cell(row=cell.row + 1, column=cell.column).value = None
    wb.save(tmp_path / "edited.xlsx")
    http = RecordedHttp(
        ("https://www.worldbank.org/", {}, "commodity_markets_page.html"),
        ("https://thedocs.worldbank.org/", {}, str(tmp_path / "edited.xlsx")),
    )

    rows = PinkSheetSource().fetch(http).set_index(["commodity", "month"])

    assert rows.loc[("cocoa", "2026-10"), "price"] == 5.75


def test_tariff_source_sends_three_digit_country_codes(tmp_path):
    http = RecordedHttp((WITS + "076/", {}, "wits_no_records.txt"), (WITS + "036/", {}, "wits_no_records.txt"))

    rows = TariffSource(countries=["BRA", "AUS"], overrides_file=tmp_path / "none.yaml").fetch(http)

    assert rows.empty  # both requests matched the zero-padded routes


def test_tariff_source_treats_a_404_for_one_country_as_no_rows(tmp_path):
    http = RecordedHttp((WITS + "643/", {}, None), (WITS + "840/", {}, "wits_trn_usa.xml"))

    rows = TariffSource(countries=["RUS", "USA"], overrides_file=tmp_path / "none.yaml").fetch(http)

    assert set(rows.importer_iso3) == {"USA"}


KCS = "https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList"


def kcs_rows():
    http = RecordedHttp((KCS, {"hsSgn": "2105", "strtYymm": "202601"}, "kcs_nitemtrade_2105_2026.xml"))
    return KcsMonthlySource(api_key="test-key", years=[2026], hs=["2105"]).fetch(http)


def test_kcs_source_reads_monthly_korea_exports_by_hs6_and_destination():
    rows = kcs_rows().set_index(["partner_iso3", "hs", "period"])

    us = rows.loc[("USA", "210500", "202610")]
    assert (us.value_usd, us.net_kg, us.flow, us.freq, us.reporter_iso3) == (4664249.0, 1078438.0, "X", "M", "KOR")
    assert rows.loc[("PHL", "210500", "202603"), "value_usd"] == 603062.0


def test_kcs_source_adds_a_world_total_per_line_and_month_and_skips_the_grand_total_row():
    rows = kcs_rows()

    world = rows[rows.partner_iso3 == "WLD"].set_index("period")
    assert world.loc["202610", "value_usd"] == 10151847.0  # sum over all 45 destinations that month
    assert not rows.period.str.contains("총계").any()
    assert set(rows.partner_iso3) <= set(CANDIDATES) | {"WLD"}


def test_kcs_source_reports_api_errors_sent_with_http_200():
    http = RecordedHttp((KCS, {}, "kcs_nitemtrade_error.xml"))

    with pytest.raises(RuntimeError, match="1년이내"):
        KcsMonthlySource(api_key="test-key", years=[2026], hs=["2105"]).fetch(http)


def test_kcs_source_queries_one_calendar_year_per_call():
    http = RecordedHttp(
        (KCS, {"strtYymm": "202501", "endYymm": "202512"}, "kcs_nitemtrade_2105_2026.xml"),
        (KCS, {"strtYymm": "202601", "endYymm": "202612"}, "kcs_nitemtrade_2105_2026.xml"),
    )

    KcsMonthlySource(api_key="test-key", years=[2025, 2026], hs=["2105"]).fetch(http)  # no unexpected request


ITEMS = "https://apis.data.go.kr/1220000/Itemtrade/getItemtradeList"
NATIONS = "https://apis.data.go.kr/1220000/nationtrade/getNationtradeList"


def test_kcs_items_source_reads_monthly_world_exports_per_hs10_product_line():
    http = RecordedHttp((ITEMS, {"hsSgn": "2105", "strtYymm": "202601"}, "kcs_itemtrade_2105_2026.xml"))

    rows = KcsItemsSource(api_key="test-key", years=[2026], hs=["2105"]).fetch(http).set_index(["hs", "period"])

    line = rows.loc[("2105001090", "202610")]
    assert (line.value_usd, line.net_kg, line.partner_iso3, line.freq) == (9207280.0, 2339473.0, "WLD", "M")
    assert rows.xs("202610", level="period").value_usd.sum() == 10151847.0  # equals the by-country world total


def test_kcs_nations_source_reads_koreas_total_monthly_exports_to_each_candidate():
    http = RecordedHttp((NATIONS, {"strtYymm": "202601", "endYymm": "202612"}, "kcs_nationtrade_2026.xml"))

    rows = KcsNationsSource(api_key="test-key", years=[2026]).fetch(http).set_index(["partner_iso3", "period"])

    ph = rows.loc[("PHL", "202601")]
    assert (ph.value_usd, ph.hs, ph.flow) == (1336850486.0, "TOTAL", "X")
    assert len(rows.index.get_level_values(0).unique()) == 30


def test_kcs_sources_without_a_key_are_skipped():
    from pipeline.sources.base import SkipSource

    for source in (KcsItemsSource(api_key=""), KcsNationsSource(api_key="")):
        with pytest.raises(SkipSource):
            source.fetch(RecordedHttp())
