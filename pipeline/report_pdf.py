"""Weekly report as a PDF (A4), built from the stored report payload with fpdf2 (pure Python, no system libraries).

A Unicode font found on the machine is embedded (Arial Unicode on macOS covers Korean; DejaVu Sans on Linux does
not). Without a Korean-capable font, Korean names are written in English rather than as empty boxes.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fpdf import FPDF
from fpdf.fonts import FontFace

FONT_CANDIDATES = [
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    Path("/Library/Fonts/Arial Unicode.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]
KOREAN = {"관세청": "Korea Customs Service"}
LATIN1 = {"→": "->", "–": "-", "—": "-", "−": "-", "·": "-", "▲": "up", "▼": "down", "…": "...", "≥": ">=", "±": "+/-"}
COMMODITY = {"cocoa": "Cocoa", "sugar_world": "Sugar (world)", "wheat_us_hrw": "Wheat (US HRW)", "palm_oil": "Palm oil"}
INK, INK_2, RULE = (11, 11, 11), (82, 81, 78), (195, 194, 183)


def destinations_line(destinations: list[dict]) -> str:
    def growth(d):
        return f"{d['growth'] * 100:+.1f}%".replace("-", "−")

    return "Fastest-growing destinations (12 months, at least US$5M): " + ", ".join(
        f"{d['name']}{' (re-export hub)' if d.get('hub') else ''} {growth(d)}" for d in destinations
    )


def _signed(n: int) -> str:
    return f"+{n}" if n > 0 else f"−{abs(n)}" if n < 0 else "0"


def find_font() -> Path | None:
    return next((p for p in FONT_CANDIDATES if p.exists()), None)


def _covers(font: Path, char: str) -> bool:
    from fontTools.ttLib import TTFont

    return ord(char) in TTFont(font, lazy=True).getBestCmap()


class _ReportPDF(FPDF):
    footer_text = ""

    def footer(self):
        self.set_y(-14)
        self.set_font(self.body_font, size=8)
        self.set_text_color(*INK_2)
        self.cell(0, 6, f"{self.footer_text}   ·   Page {self.page_no()} of {{nb}}", align="C")


def to_pdf(report: dict, font: Path | None | str = "auto") -> bytes:
    font = find_font() if font == "auto" else font
    korean = bool(font) and _covers(font, "관")

    def t(text) -> str:
        """Text the chosen font can draw."""
        text = str(text)
        if not korean:
            for ko, en in KOREAN.items():
                text = text.replace(ko, en)
        if not font:
            for u, a in LATIN1.items():
                text = text.replace(u, a)
            text = text.encode("latin-1", "replace").decode("latin-1")
        return text

    pdf = _ReportPDF(format="A4")
    pdf.set_margins(18, 18, 18)
    pdf.set_auto_page_break(True, margin=20)
    if font:
        pdf.add_font("body", "", str(font))
        pdf.add_font("body", "B", str(font))  # single-weight font: headings stand out by size and colour
        pdf.body_font = "body"
    else:
        pdf.body_font = "helvetica"
    title = f"WellGTM weekly report: {report['title']}"
    pdf.set_title(t(title))
    pdf.set_author("WellGTM pipeline")
    pdf.set_lang("en")
    pdf.footer_text = t(f"WellGTM weekly report · {report['title']}")
    pdf.add_page()
    width = pdf.epw

    def text(s, size=10, color=INK, gap=1.5, style=""):
        pdf.set_font(pdf.body_font, style, size)
        pdf.set_text_color(*color)
        pdf.multi_cell(width, size * 0.5, t(s), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(gap)

    def heading(s):
        pdf.ln(3)
        text(s, size=13, style="B", gap=0.5)
        pdf.set_draw_color(*RULE)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + width, pdf.get_y())
        pdf.ln(2.5)

    def table(header, rows, widths):
        pdf.set_font(pdf.body_font, size=9)
        pdf.set_text_color(*INK)
        with pdf.table(
            col_widths=widths,
            text_align="LEFT",
            line_height=5,
            padding=1.2,
            headings_style=FontFace(emphasis=None, color=INK_2, fill_color=(241, 240, 236)),
            borders_layout="HORIZONTAL_LINES",
        ) as tbl:
            for row in [header, *rows]:
                r = tbl.row()
                for cell in row:
                    r.cell(t(cell))
        pdf.ln(2)

    def pct(v):
        return "n/a" if v is None else f"{v * 100:+.1f}%".replace("-", "−")

    def usd(v):
        return f"US${v / 1e6:,.1f}M" if v >= 1e6 else f"US${v:,.0f}"

    # ---- title block ----
    text("WellGTM weekly report", size=9, color=INK_2, gap=0)
    text(report["title"], size=20, style="B", gap=1)
    text(report["headline"], size=11, gap=1)
    generated = datetime.fromisoformat(report["generated_at"]).strftime("%d %b %Y, %H:%M UTC")
    text(
        f"Generated automatically on {generated} from the WellGTM pipeline. Every number comes from stored data.",
        size=8.5,
        color=INK_2,
        gap=1,
    )

    heading("TOP3")
    table(
        ["#", "Market", "Score", "Confidence", "Why"],
        [[c["rank"], c["name"], f"{c['score']:.1f}", c["confidence"], c["headline"]] for c in report["top3"]],
        (6, 22, 11, 22, 64),
    )

    heading("Rank changes")
    if not report.get("new_month"):
        text("No new monthly data this week; 관세청 publishes the next month around the 15th.")
    elif report["movers"]:
        text(f"Month on month, {report['month_label']} data:", gap=1)
        table(
            ["Market", "Last month", "Now", "Change"],
            [[m["name"], f"#{m['was']}", f"#{m['now']}", _signed(m["change"])] for m in report["movers"]],
            (50, 25, 25, 25),
        )
    else:
        text(f"No rank changes, {report['month_label']} data.")

    heading("Alerts")
    alerts = report.get("alerts") or []
    if alerts:
        for a in alerts:
            text(f"•  {a['name']}: {a['text']}", gap=0.6)
    else:
        text("No alerts for the top 10 markets this week.")

    heading("Exports")
    e = report.get("exports")
    if e:
        text(
            f"Korea's K-food exports in {e['period'][:4]}-{e['period'][4:]}: {usd(e['value_usd'])} "
            f"({pct(e['yoy'])} on a year earlier; 관세청).",
            gap=1,
        )
        table(
            ["Category", "Exports", "vs a year earlier"],
            [[c["name"], usd(c["value_usd"]), pct(c["yoy"])] for c in e["by_category"].values()],
            (50, 35, 35),
        )
        if e["fastest_destinations"]:
            text(destinations_line(e["fastest_destinations"]))
    else:
        text("No 관세청 monthly data loaded.")

    heading("Forecast")
    f = report.get("forecast")
    if f:
        text(
            f"Most likely TOP3 in {f['year']}: "
            + ", ".join(f"{c['name']} ({c['p_top3'] * 100:.0f}%)" for c in f["top3"])
            + ".",
            gap=1,
        )
        h = f["holdout"]
        text(
            f"Accuracy check: forecasting {h['year']} from {h['trained_on']} predicted "
            f"{', '.join(h['predicted_top3'])}; actual {', '.join(h['actual_top3'])}.",
            size=9,
            color=INK_2,
        )
    else:
        text("No forecast yet.")

    heading("Ingredient prices")
    if report["prices"]:
        table(
            ["Commodity", "Latest", "Month", "vs a year earlier"],
            [
                [
                    COMMODITY.get(p["commodity"], p["commodity"]),
                    f"{p['latest']:.2f} {p['unit']}",
                    p["latest_month"],
                    pct(p["yoy"]),
                ]
                for p in report["prices"]
            ],
            (45, 35, 25, 35),
        )
    else:
        text("No price data.")

    heading("Data and pipeline")
    h = report["health"]
    text(
        f"{h['runs']} runs this week, {h['failed']} failed; {h['rows_new']:,} new rows, "
        f"{h['rows_revised']:,} revised values.",
        gap=1,
    )
    if h["skipped"]:
        text(f"Skipped: {', '.join(h['skipped'])}.", gap=1)
    if h["fta_rates_missing"]:
        text(
            f"FTA preferential rates not yet entered for: {', '.join(h['fta_rates_missing'])} "
            "(applied tariffs shown as MFN).",
            size=9,
            color=INK_2,
        )

    return bytes(pdf.output())
