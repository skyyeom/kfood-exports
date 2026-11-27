from pipeline.sources.comtrade import ComtradeSource
from pipeline.sources.fx import FxSource
from pipeline.sources.kcs_monthly import KcsItemsSource, KcsMonthlySource, KcsNationsSource
from pipeline.sources.pinksheet import PinkSheetSource
from pipeline.sources.tariffs import TariffSource
from pipeline.sources.wdi import WdiSource

SOURCES = {
    s.name: s
    for s in (
        ComtradeSource,
        FxSource,
        KcsItemsSource,
        KcsMonthlySource,
        KcsNationsSource,
        PinkSheetSource,
        TariffSource,
        WdiSource,
    )
}
