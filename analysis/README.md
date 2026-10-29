# Exploratory analysis

Reproducible data pulls and analysis behind [docs/pm/03_data_analysis.md](../docs/pm/03_data_analysis.md).
This is discovery work, not product code. The production pipeline will be built in `pipeline/` (milestone M1).

```bash
python3 -m venv .venv && .venv/bin/pip install -r analysis/requirements.txt
.venv/bin/python analysis/collect.py   # pulls UN Comtrade + World Bank → analysis/data/*.csv
.venv/bin/python analysis/analyze.py   # tables → analysis/output/, charts → docs/pm/figures/
```

- `collect.py` uses only public, keyless APIs (UN Comtrade public preview, World Bank). The Comtrade preview allows one year per call and 500 rows per response.
- Every raw row stores `source` and `retrieved_at`.

## PM artefacts for Microsoft tools
```bash
.venv/bin/python analysis/build_pm_artifacts.py   # needs analyze.py outputs
```
This generates the Excel workbook, the Microsoft Forms survey (.docx), the MS Project XML/CSV and the roadmap Gantt PNG in `docs/pm/workbooks/` and `docs/pm/figures/`.
- Roadmap and survey definitions: `pm_config.py`
- Competitor and trend data: `pm_competitors.py`
