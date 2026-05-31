"""
build_html.py
-------------
Converts report/Project_Report.md into a professional, print-ready, self-contained
HTML file (report/Project_Report.html). All figures are base64-embedded so the single
HTML file can be opened in any browser and exported to PDF (Ctrl/Cmd+P -> Save as PDF)
or opened in Microsoft Word.

Run:  python3 analysis/build_html.py
"""

import base64
import os
import re
import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD_PATH = os.path.join(ROOT, "report", "Project_Report.md")
OUT_PATH = os.path.join(ROOT, "report", "Project_Report.html")
FIG_DIR = os.path.join(ROOT, "figures")

with open(MD_PATH, encoding="utf-8") as f:
    md_text = f.read()

# Convert Markdown -> HTML body
html_body = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "attr_list", "md_in_html", "sane_lists"],
)

# Embed images as base64 data URIs (resolve ../figures/x.png -> figures/x.png)
def embed_image(match):
    src = match.group(1)
    fname = os.path.basename(src)
    path = os.path.join(FIG_DIR, fname)
    if not os.path.exists(path):
        return match.group(0)
    with open(path, "rb") as img:
        b64 = base64.b64encode(img.read()).decode("ascii")
    return f'src="data:image/png;base64,{b64}"'

html_body = re.sub(r'src="(\.\./figures/[^"]+)"', embed_image, html_body)

CSS = """
:root { --primary:#1f4e79; --accent:#e07b39; --ink:#222; --muted:#666; }
* { box-sizing: border-box; }
body {
  font-family: Georgia, 'Times New Roman', serif;
  color: var(--ink); line-height: 1.55; font-size: 12pt;
  background: #e9eaed; margin: 0;
}
.page {
  background: #fff; max-width: 210mm; margin: 18px auto; padding: 26mm 22mm 24mm 26mm;
  box-shadow: 0 2px 14px rgba(0,0,0,0.18);
}
h1 { color: var(--primary); font-size: 19pt; line-height: 1.25; margin: 0.2em 0 0.5em;
     border-bottom: 3px solid var(--primary); padding-bottom: 6px; }
h2 { color: var(--primary); font-size: 15pt; margin: 1.1em 0 0.4em; }
h3 { color: #2c3e50; font-size: 13pt; margin: 1em 0 0.3em; }
h4 { color: #2c3e50; font-size: 12pt; margin: 0.9em 0 0.3em; font-style: italic; }
p { text-align: justify; margin: 0.5em 0; }
a { color: var(--primary); }
blockquote {
  border-left: 4px solid var(--accent); background: #faf6f2; margin: 0.8em 0;
  padding: 0.5em 0.9em; color: #574; font-style: italic; font-size: 11pt;
}
code, pre { font-family: 'DejaVu Sans Mono','Consolas',monospace; }
pre {
  background: #f5f7fa; border: 1px solid #d6dde6; border-radius: 4px;
  padding: 12px; font-size: 8.5pt; line-height: 1.25; overflow-x: auto;
  white-space: pre; page-break-inside: avoid; color: #1c2b3a;
}
table {
  border-collapse: collapse; width: 100%; margin: 0.8em 0; font-size: 10pt;
  page-break-inside: avoid;
}
th, td { border: 1px solid #b9c4d0; padding: 5px 8px; text-align: left; vertical-align: top; }
th { background: var(--primary); color: #fff; font-family: Arial, sans-serif; font-size: 9.5pt; }
tr:nth-child(even) td { background: #f3f6fa; }
img { max-width: 96%; display: block; margin: 0.6em auto 0.2em; page-break-inside: avoid;
      border: 1px solid #e3e3e3; }
em { color: var(--muted); }
hr { border: none; border-top: 1px solid #ccc; margin: 1.5em 0; }

/* Page-break control */
.pagebreak { page-break-before: always; break-before: page; }
h1 { page-break-after: avoid; }
h2, h3, h4 { page-break-after: avoid; }

/* Title page */
.titlepage { text-align: center; padding-top: 8mm; }
.titlepage h1 { border: none; color: var(--primary); font-size: 20pt; margin-top: 0.3em; }
.titlepage h2 { color: #111; font-size: 16pt; }
.titlepage h3 { color: #333; font-weight: normal; font-size: 12.5pt; }
.titlepage p { text-align: center; }
.titlepage strong { font-size: 12.5pt; }

/* Front-matter certificates */
.frontmatter h2 { text-align: center; letter-spacing: 1px; border-bottom: 1px solid #ccc;
                  padding-bottom: 6px; }
.signtable { width: 100%; border: none; margin-top: 30px; }
.signtable td { border: none; width: 50%; vertical-align: top; padding-top: 28px; }
tr:nth-child(even) .signtable td { background: transparent; }

@media print {
  body { background: #fff; }
  .page { box-shadow: none; margin: 0; max-width: none; width: auto;
          padding: 0; }
  @page { size: A4; margin: 30mm 22mm 26mm 36mm; }
  a { color: #000; text-decoration: none; }
  table, img, pre, blockquote { page-break-inside: avoid; }
}
"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MBA Project Report — Social Media &amp; Digital Marketing Analytics</title>
<style>{CSS}</style>
</head>
<body>
<div class="page">
{html_body}
</div>
</body>
</html>
"""

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)

size_kb = os.path.getsize(OUT_PATH) / 1024
print(f"Built {OUT_PATH} ({size_kb:.0f} KB)")
img_count = html.count("data:image/png;base64,")
print(f"Embedded {img_count} figures as base64.")

# Optionally render a PDF (requires WeasyPrint + system Pango/Cairo libraries)
PDF_PATH = os.path.join(ROOT, "report", "Project_Report.pdf")
try:
    from weasyprint import HTML
    HTML(string=html, base_url=ROOT).write_pdf(PDF_PATH)
    print(f"Built {PDF_PATH} ({os.path.getsize(PDF_PATH)/1024:.0f} KB)")
except Exception as exc:  # pragma: no cover
    print(f"PDF not generated (WeasyPrint unavailable): {exc}")
    print("You can still export the HTML to PDF from any browser (Print -> Save as PDF).")
