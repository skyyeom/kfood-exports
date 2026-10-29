"""Single source of truth for the WellGTM roadmap and client survey.

Imported by build_pm_artifacts.py to generate:
- docs/pm/workbooks/WellGTM_market_research.xlsx (Roadmap, Survey_* sheets)
- docs/pm/workbooks/WellGTM_client_survey_for_MS_Forms.docx
- docs/pm/workbooks/WellGTM_roadmap_MSProject.xml (+ CSV)
- docs/pm/figures/roadmap_gantt.png
"""

from __future__ import annotations

from datetime import date

# Roadmap: anticipated windows, to be re-baselined against the official challenge schedule.
# (id, name, horizon, theme, start, finish, milestone?, predecessors, client_objective, pct_complete)
ROADMAP = [
    ("H1", "Horizon 1 — Prove (Lotte AX Challenge)", "H1", "Summary", date(2026, 10, 26), date(2027, 4, 9), False, [], "", None),
    ("R0", "R0 Discovery & PM artefacts", "H1", "Product", date(2026, 10, 26), date(2026, 10, 30), False, [], "Grounded problem & requirements", 100),
    ("M1", "M1 Data foundation (schema, pipeline, provenance, tariffs)", "H1", "Data", date(2026, 11, 2), date(2026, 11, 13), False, ["R0"], "Trusted evidence base", 0),
    ("M2", "M2 Scoring, P(TOP3), presets, forecast engine", "H1", "Intelligence", date(2026, 11, 16), date(2026, 11, 27), False, ["M1"], "Defensible TOP3", 0),
    ("M3", "M3 API + dashboard MVP (KO/EN, warm-up)", "H1", "Experience", date(2026, 11, 30), date(2026, 12, 11), False, ["M2"], "Decision speed", 0),
    ("M4", "M4 AI agent, verifier, regulation RAG, TOP3 report", "H1", "AI agent", date(2026, 12, 14), date(2027, 1, 8), False, ["M3"], "Trusted AI answers", 0),
    ("R10", "◆ R1.0 예선 demo-ready", "H1", "Milestone", date(2027, 1, 8), date(2027, 1, 8), True, ["M4"], "", 0),
    ("M5", "M5 Monitoring: auth, daily refresh, alerts, simulation", "H1", "Monitoring", date(2027, 1, 11), date(2027, 1, 29), False, ["R10"], "Market visibility", 0),
    ("M6", "M6 Evaluation reports, time-savings, proposal, video", "H1", "Product", date(2027, 2, 1), date(2027, 2, 12), False, ["M5"], "Credible impact claims", 0),
    ("R11", "◆ R1.1 예선 submission (anticipated)", "H1", "Milestone", date(2027, 2, 12), date(2027, 2, 12), True, ["M6"], "", 0),
    ("R20", "R2.0 본선 prototype: Lotte field data, product mapping", "H1", "Data", date(2027, 3, 1), date(2027, 4, 2), False, ["R11"], "Internal data loop", 0),
    ("R2M", "◆ 본선 demo (anticipated)", "H1", "Milestone", date(2027, 4, 9), date(2027, 4, 9), True, ["R20"], "", 0),
    ("H2", "Horizon 2 — Embed (pilot at Lotte Wellfood)", "H2", "Summary", date(2027, 5, 3), date(2027, 11, 30), False, [], "", None),
    ("R30", "R3.0 Enterprise pilot: SSO, security review, internal sales connector", "H2", "Platform", date(2027, 5, 3), date(2027, 7, 30), False, ["R2M"], "Overseas share 35% by 2028", 0),
    ("R31", "R3.1 Product × market × entry-mode economics (Pepero, ZERO, ice cream)", "H2", "Intelligence", date(2027, 6, 1), date(2027, 8, 27), False, ["R2M"], "Pepero global mega brand", 0),
    ("R40", "R4.0 Production rollout; used in annual market-priority review", "H2", "Platform", date(2027, 9, 1), date(2027, 11, 30), False, ["R30", "R31"], "Disciplined portfolio decisions", 0),
    ("R4M", "◆ R4.0 in production", "H2", "Milestone", date(2027, 11, 30), date(2027, 11, 30), True, ["R40"], "", 0),
    ("H3", "Horizon 3 — Scale (multi-tenant SaaS)", "H3", "Summary", date(2028, 1, 3), date(2028, 12, 31), False, [], "", None),
    ("R50", "R5.0 Multi-tenant SaaS beta; new categories; premium data connectors", "H3", "Platform", date(2028, 1, 3), date(2028, 6, 30), False, ["R4M"], "Scale beyond one company", 0),
    ("R51", "R5.1 Export-support organisation pilot", "H3", "GTM", date(2028, 4, 3), date(2028, 9, 29), False, ["R4M"], "SME export enablement", 0),
    ("R60", "◆ R6.0 General availability", "H3", "Milestone", date(2028, 12, 15), date(2028, 12, 15), True, ["R50", "R51"], "", 0),
    ("OBJ", "◆ Client objective: Lotte overseas revenue share 35% (2028)", "H3", "Client objective", date(2028, 12, 31), date(2028, 12, 31), True, [], "", None),
]

PERSONAS = [
    "Global Market Strategy Manager",
    "Export Sales Manager",
    "Sales Operations / Business Analyst",
    "Regulatory Affairs / QA",
    "Procurement / Raw Materials",
    "Executive (Head of Global Business)",
    "Export-support organisation advisor",
    "Other",
]

LIKERT = ["1 - Not at all", "2", "3", "4", "5 - Extremely"]

# Survey: (id, section, type, question, options)
# type: choice | multi | likert | text
SURVEY = [
    ("Q1", "A. About you", "choice", "Which best describes your role?", PERSONAS),
    ("Q2", "A. About you", "choice", "What type of organisation do you work for?",
     ["Large food/consumer-goods manufacturer", "Mid-size or small food manufacturer",
      "Distributor / trading company", "Export-support agency or association", "Other"]),
    ("Q3", "A. About you", "choice", "How many export markets does your business currently sell to?",
     ["1-5", "6-15", "16-30", "More than 30", "Don't know"]),
    ("Q4", "A. About you", "choice", "How involved are you in choosing which export markets to prioritise?",
     ["I make or approve the decision", "I prepare the analysis/recommendation",
      "I provide input (e.g. sales, regulatory)", "I execute after the decision", "Not involved"]),
    ("Q5", "B. Current process", "choice", "How often does your team run an export-market prioritisation study?",
     ["Monthly or more", "Quarterly", "Once or twice a year", "Only when a specific opportunity arises", "Never"]),
    ("Q6", "B. Current process", "choice", "How long does one market-prioritisation study usually take end-to-end?",
     ["Less than 1 week", "1-2 weeks", "3-4 weeks", "5-8 weeks", "More than 8 weeks"]),
    ("Q7", "B. Current process", "multi", "Which sources do you use today? (select all that apply)",
     ["UN Comtrade / ITC Trade Map", "Korea Customs / KITA trade statistics", "aT KATI", "KOTRA reports",
      "Euromonitor / Mintel / Statista", "Consultants", "Distributor or partner feedback", "Internal sales data",
      "News / social media"]),
    ("Q8", "C. Pain points", "likert", "Collecting and reconciling data from different sources takes too much time.", LIKERT),
    ("Q9", "C. Pain points", "likert", "Our market recommendations are challenged because the weighting/criteria are not explicit.", LIKERT),
    ("Q10", "C. Pain points", "likert", "We learn about tariff or regulation changes in our markets too late.", LIKERT),
    ("Q11", "C. Pain points", "likert", "Market studies are out of date soon after they are finished.", LIKERT),
    ("Q12", "C. Pain points", "likert", "It is hard to find reliable, sourced import regulations for a specific country and product.", LIKERT),
    ("Q13", "D. Feature value", "likert", "How valuable: a ranking of export markets with adjustable criteria weights?", LIKERT),
    ("Q14", "D. Feature value", "likert", "How valuable: seeing how robust the TOP3 is (probability of staying TOP3 if weights change)?", LIKERT),
    ("Q15", "D. Feature value", "likert", "How valuable: an AI assistant (Korean/English) that answers with cited sources?", LIKERT),
    ("Q16", "D. Feature value", "likert", "How valuable: e-mail alerts when something changes in markets you watch?", LIKERT),
    ("Q17", "D. Feature value", "likert", "How valuable: one-click TOP3 recommendation report (PDF) with sources?", LIKERT),
    ("Q18", "E. Trust & adoption", "likert", "I would trust AI-generated market insights if every number links to its source.", LIKERT),
    ("Q19", "E. Trust & adoption", "multi", "What would stop you from using a tool like this? (select all that apply)",
     ["Accuracy concerns", "Data security / confidentiality", "Does not fit our workflow", "Language support",
      "Cost", "Too many alerts", "Prefer consultants", "Nothing"]),
    ("Q20", "E. Trust & adoption", "text", "What is the single biggest problem you face when deciding where to export next?", []),
    ("Q21", "E. Trust & adoption", "choice", "May we contact you for a 30-minute follow-up interview?", ["Yes", "No"]),
]
