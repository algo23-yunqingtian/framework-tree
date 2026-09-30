#!/usr/bin/env python3
"""Probe PDF structure — inspect chart patterns, titles, legends on sample pages."""
import pdfplumber
import sys, os

os.environ['PYTHONIOENCODING'] = 'utf-8'

PDF_PATH = r"D:\DSH_WORK\周报\PDFs\铝周报20260830.pdf"

with pdfplumber.open(PDF_PATH) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    print("="*80)
    
    for i in [7, 8, 9, 26, 27, 30, 31]:
        page = pdf.pages[i]
        txt = page.extract_text()
        print(f"\n=== Page {i+1} (first 2000 chars) ===")
        if txt:
            # print lines
            for line in txt.split('\n')[:80]:
                print(line)
        else:
            print("(empty)")
        print("-"*80)
