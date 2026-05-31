"""
restyle_dpu.py
--------------
Post-processes the existing DPU COL formatted HTML files so they:
  1. show the official Dr. D. Y. Patil Vidyapeeth logo on the cover page,
  2. flow continuously (chapter content no longer forced onto separate full
     pages -> removes the large blank gaps), while keeping each front-matter
     certificate/declaration on its own page (as the institute sample requires),
  3. carry clean, auto-numbered page footers.

It then renders print-ready PDFs with WeasyPrint.

Run:  python3 analysis/restyle_dpu.py
"""

import base64
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(ROOT, "assets", "dpu_logo.png")

with open(LOGO, "rb") as f:
    LOGO_B64 = base64.b64encode(f.read()).decode("ascii")
LOGO_TAG = f'<img class="cover-logo" src="data:image/png;base64,{LOGO_B64}" alt="Dr. D. Y. Patil Vidyapeeth, Centre for Online Learning, Pune"/>'

# ---------------------------------------------------------------- shared CSS
COMMON_CSS = """
  * { margin: 0; padding: 0; box-sizing: border-box; }
  @page {
    size: A4;
    margin: 22mm 20mm 18mm 26mm;
    @bottom-center { content: counter(page); font-family: "Times New Roman", Times, serif; font-size: 11pt; }
  }
  @page :first { @bottom-center { content: ""; } }
  body { font-family: "Times New Roman", Times, serif; font-size: 12pt; color: #000; line-height: 1.5; background: #fff; }

  /* Flowing content: no forced full-page boxes -> no blank gaps */
  .page { display: block; }
  /* Front-matter sections (cover, declaration, certificate, etc.) keep one per page */
  .page.fm { page-break-after: always; }
  /* Each chapter starts on a fresh page; its content then flows naturally */
  .page.ch { page-break-before: always; }

  h1.chapter { font-size: 15pt; font-weight: bold; text-align: center; margin: 4px 0 2px 0; text-transform: uppercase; }
  h1.ctitle  { font-size: 13.5pt; font-weight: bold; text-align: center; margin: 0 0 16px 0; }
  h1.section { font-size: 15pt; font-weight: bold; text-align: center; margin: 6px 0 16px 0; text-transform: uppercase; letter-spacing: 1px; }
  h1 { font-size: 14pt; font-weight: bold; text-align: center; margin: 8px 0 12px 0; text-transform: uppercase; }
  h2 { font-size: 12.5pt; font-weight: bold; margin: 14px 0 6px 0; page-break-after: avoid; }
  h3 { font-size: 12pt; font-weight: bold; font-style: italic; margin: 10px 0 5px 0; page-break-after: avoid; }
  p  { text-align: justify; margin-bottom: 9px; text-indent: 28px; }
  p.noindent, p.center { text-indent: 0; }
  p.center { text-align: center; }
  .center { text-align: center; }
  .bold { font-weight: bold; }
  ul, ol { margin: 6px 0 10px 30px; }
  li { margin-bottom: 5px; text-align: justify; }
  table { width: 100%; border-collapse: collapse; margin: 10px 0; page-break-inside: avoid; }
  th, td { border: 1px solid #000; padding: 5px 8px; font-size: 11pt; vertical-align: top; }
  th { font-weight: bold; background: #eaeaea; text-align: center; }
  td.l { text-align: left; } td.c { text-align: center; }

  /* Cover */
  .cover { text-align: center; padding-top: 4mm; }
  .cover-logo { display:block; width: 150mm; max-width: 96%; margin: 0 auto 10px auto; }
  .cover .title { font-size: 16pt; font-weight: bold; margin: 14px 0 22px 0; text-transform: uppercase; line-height: 1.4; }
  .cover .line  { font-size: 12.5pt; margin: 3px 0; }
  .cover .big   { font-size: 13.5pt; font-weight: bold; margin: 5px 0; line-height: 1.4; }
  .cover .field { font-size: 13pt; margin: 2px 0; font-weight: bold; }
  .sp, .spacer { height: 14px; }
  .sig-row { display: flex; justify-content: space-between; margin-top: 36px; }

  /* CSS bar charts */
  .bar-chart { display:flex; align-items:flex-end; gap:16px; height:170px; border-bottom:2px solid #000; margin:16px 0 30px 24px; padding-top:6px; page-break-inside: avoid; }
  .bar-wrap { display:flex; flex-direction:column; align-items:center; }
  .bar { width:46px; background:#37474f; color:#fff; font-size:9pt; text-align:center; padding-top:3px; }
  .bar-label { font-size:8.5pt; margin-top:6px; max-width:64px; text-align:center; }
"""


def restyle(html, *, is_report):
    # 1. Replace the entire <style>...</style> with our CSS.
    html = re.sub(r"<style>.*?</style>", f"<style>{COMMON_CSS}</style>", html, count=1, flags=re.S)

    # 2. Remove hard-coded page-number divs (we now auto-number via @page).
    html = re.sub(r'<div class="pgno">[^<]*</div>\s*', "", html)

    # 3. Tag the cover page and inject the logo.
    html = re.sub(
        r'<div class="page">\s*<div class="cover">',
        '<div class="page fm">\n  <div class="cover">\n    ' + LOGO_TAG,
        html, count=1,
    )

    if is_report:
        # Front-matter sections (Declaration, Certificate, Acknowledgement,
        # TOC, lists, Abbreviations, Abstract) -> one per page.
        html = re.sub(r'<div class="page">\s*<h1 class="section">',
                      '<div class="page fm">\n  <h1 class="section">', html)
        # Chapter opening pages -> page break before, then flow.
        html = re.sub(r'<div class="page">\s*<h1 class="chapter">',
                      '<div class="page ch">\n  <h1 class="chapter">', html)
        # Any remaining bare ".page" divs are continuation content -> flow (no class change needed).
    else:
        # Proposal: cover already tagged; let the rest flow continuously.
        # Index gets its own page; numbered sections start on a fresh page but flow after.
        html = re.sub(r'<div class="page">\s*<h1>Index</h1>',
                      '<div class="page ch">\n  <h1>Index</h1>', html, count=1)
        html = re.sub(r'<div class="page">\s*<h1>(\d+\.)',
                      r'<div class="page ch">\n  <h1>\1', html)

    return html


def build(src_html, out_html, out_pdf, *, is_report):
    # Keep a pristine backup of the original so re-runs are idempotent.
    backup = src_html.replace(".html", ".orig.html")
    if not os.path.exists(backup):
        with open(src_html, encoding="utf-8") as f:
            open(backup, "w", encoding="utf-8").write(f.read())
    with open(backup, encoding="utf-8") as f:
        html = f.read()
    html = restyle(html, is_report=is_report)
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    from weasyprint import HTML
    HTML(string=html, base_url=ROOT).write_pdf(out_pdf)
    print(f"  built {os.path.basename(out_pdf)} ({os.path.getsize(out_pdf)//1024} KB)")


if __name__ == "__main__":
    print("Restyling DPU report and proposal (logo + continuous flow)...")
    build(os.path.join(ROOT, "Project_Report_OMBP405.html"),
          os.path.join(ROOT, "Project_Report_OMBP405.html"),
          os.path.join(ROOT, "Project_Report_OMBP405.pdf"), is_report=True)
    build(os.path.join(ROOT, "Research_Proposal_OMBP405.html"),
          os.path.join(ROOT, "Research_Proposal_OMBP405.html"),
          os.path.join(ROOT, "Research_Proposal_OMBP405.pdf"), is_report=False)
    print("Done.")
