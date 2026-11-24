from pipeline.sources.comtrade import ComtradeSource
from pipeline.sources.fx import FxSource
from pipeline.sources.kcs_monthly import KcsMonthlySource
from pipeline.sources.pinksheet import PinkSheetSource
from pipeline.sources.tariffs import TariffSource
from pipeline.sources.wdi import WdiSource

SOURCES = {s.name: s for s in (ComtradeSource, FxSource, KcsMonthlySource, PinkSheetSource, TariffSource, WdiSource)}
