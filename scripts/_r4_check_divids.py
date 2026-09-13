#!/usr/bin/env python3
"""R4: 检查非标准 div-id 命名"""
import re, glob, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
html_files = sorted(glob.glob(os.path.join(BASE, '*.html')))
html_files = [f for f in html_files if 'index.html' not in f and 'export_selector' not in f and 'legacy' not in f]

# Standard pattern: echart_xx_n_cN (e.g. echart_cu_2_1_c3)
standard_pat = re.compile(r'^echart_[a-z]{2}_[0-9]+(?:_[0-9]+)*_c\d+$')

non_standard = []
for hf in html_files:
    html = open(hf, encoding='utf-8').read()
    fname = os.path.basename(hf)
    divs = re.findall(r'<div id="([^"]+)"', html)
    for d in divs:
        if d.startswith('echart_') and not standard_pat.match(d):
            non_standard.append((fname, d))

print(f"Found {len(non_standard)} non-standard chart div-ids:")
for f, d in non_standard:
    print(f"  {f}: {d}")

# Also find charts missing div ids (div without id)
no_id_charts = []
for hf in html_files:
    html = open(hf, encoding='utf-8').read()
    fname = os.path.basename(hf)
    # Find chart divs that don't have id attribute
    chart_blocks = re.findall(r'<div class="chart">(.*?)(?=<div class="chart">|<div class="note">|$)', html, re.DOTALL)
    for i, block in enumerate(chart_blocks):
        if not re.search(r'<div id="echart_', block):
            no_id_charts.append((fname, i+1, block[:100]))

print(f"\nFound {len(no_id_charts)} charts without echart div-id:")
for f, seq, snippet in no_id_charts:
    print(f"  {f} C{seq}: {snippet[:60]}...")