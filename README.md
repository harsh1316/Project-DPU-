# MBA Project — Social Media & Digital Marketing Analytics

**A Study on the Impact of Social Media and Digital Marketing Analytics on Consumer Engagement and Brand Performance**

MBA (Online) — Business Analytics specialization | Course OMBP 405 — Project Work | 2024–2026
Student ID: 241116868 · PRN: 240502009463 · Mentor: Ms. Reshma Y. Sayyed

---

## 📄 The Report (start here)

| File | Description |
|---|---|
| **[report/Project_Report.pdf](report/Project_Report.pdf)** | **Final 81-page report, A4, print-ready — submit this** |
| [report/Project_Report.html](report/Project_Report.html) | Self-contained version (open in any browser; importable to Word) |
| [report/Project_Report.md](report/Project_Report.md) | Editable Markdown source |

> To download: open the PDF above and click the **Download** (⬇) button on GitHub, or use **Code → Download ZIP** on the repo home page to get everything.

## 📊 Datasets (`data/`)
- `survey_responses.csv` — 270 primary survey responses
- `campaign_performance.csv` — 12-month × 5-platform campaign metrics
- `platform_summary.csv` — aggregated KPI summary by platform

## 📈 Figures (`figures/`)
17 charts and 2 composite dashboards used throughout the report.

## 🔬 Reproducibility (`analysis/`)
- `generate_project.py` — generates datasets, runs all statistics, builds figures
- `build_html.py` — renders the report to HTML and PDF
- `results.json` — every statistic cited in the report

Rebuild from scratch:
```bash
pip install pandas numpy scipy matplotlib markdown weasyprint
python3 analysis/generate_project.py
python3 analysis/build_html.py
```

## Key findings
- Sample n = 270 (79.4% response rate); scale reliability Cronbach's α = 0.889
- Regression R² = 0.581 (p < 0.001) — engagement attitudes strongly predict purchase
- Age does **not** significantly determine purchase (χ², p = 0.24)
- Trust–value gap: analytics valued highest (3.93) vs. trust in ads lowest (2.83)
- Campaign: 21.76M impressions, overall ROAS 4.45×

---
*Before submitting, replace the placeholders in the report: `[Student Name]`, `[Name of University / Institute]`, `[Programme Director / HOD]`, then rebuild the PDF.*
