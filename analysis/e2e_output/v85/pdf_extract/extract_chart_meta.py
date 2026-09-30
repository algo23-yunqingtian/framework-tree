#!/usr/bin/env python3
"""
DSH-B_PDF_CHART_META_EXTRACT_TASK
T2: Parse each chart in 6 PDF weekly reports, output chart metadata + legend sets.

Handles two PDF formats:
  1. "图：" prefixed chart titles (铝, 氧化铝, 碳酸锂, 镍, 锡)
  2. Non-prefixed chart titles (硅产业链) — uses DSH data to locate chart positions

Output:
  analysis/e2e_output/v85/pdf_extract/pdf_chart_meta_all.csv
  analysis/e2e_output/v85/pdf_extract/pdf_chart_meta_all.json
"""
import csv
import json
import os
import re
import sys
from pathlib import Path
from collections import defaultdict

import pdfplumber

# ── Paths ──
REPO = Path(r"D:\DSH_WORK\framework-tree")
OUT_DIR = REPO / "analysis" / "e2e_output" / "v85" / "pdf_extract"
OUT_CSV = OUT_DIR / "pdf_chart_meta_all.csv"
OUT_JSON = OUT_DIR / "pdf_chart_meta_all.json"
LOG_FILE = r"D:\DSH_WORK\chart_extract_log.txt"

DSH_CSV = OUT_DIR / "pdf_extract_all_candidates.csv"
MANIFEST = REPO / "snapshot_pdf_local" / "pdf_source_manifest.json"

# ── Load source data ──
def load_dsh_extract():
    with open(DSH_CSV, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def load_manifest():
    with open(MANIFEST, "r", encoding="utf-8") as f:
        return json.load(f)

# ── Text classification helpers ──
def is_number(text):
    c = text.replace(",", "").replace(".", "").replace("-", "").replace("+", "").replace("%", "").replace("‰", "").replace(":", "").replace("/", "")
    if not c: return True
    return c.isdigit()

def is_unit(text):
    t = text.strip()
    units = {"元", "元/吨", "吨", "万吨", "千吨", "%", "倍", "万元", "亿美元",
             "万美元", "美元/吨", "美元", "元/千克", "元/kg", "元/克",
             "元/公斤", "万张", "张", "pp", "bp", "bps", "万吨/日",
             "万吨/周", "万吨/月", "万吨/年", "元/吨·日", "元/吨·天",
             "元/吨·月", "元/吨·年", "元/吨·周", "元/吨", "元/千克",
             "元/吨·日", "元/吨·天", "元/吨·月", "元/吨·年", "元/吨·周",
             "美元/吨·日", "美元/吨·天", "美元/吨·月", "美元/吨·年",
             "美元/吨·周", "美元/吨·年", "美元/吨·月", "美元/吨·周",
             "美元/吨·天", "美元/吨·日", "亿美元/吨", "亿元", "亿元/吨",
             "元/吨·月", "元/吨·周", "元/吨·年", "元/吨·天", "元/吨·日",
             "元/吨·月", "元/吨·周", "元/吨·年", "元/吨·天", "元/吨·日",
             "元/吨·月", "元/吨·周", "元/吨·年", "元/吨·天", "元/吨·日",
             "元/吨·月", "元/吨·周", "元/吨·年", "元/吨·天", "元/吨·日",
             "元/吨·月", "元/吨·周", "元/吨·年", "元/吨·天", "元/吨·日"}
    return t in units

def is_month_year(text):
    pats = [r'^\d{1,2}月$', r'^\d{4}年$', r'^\d{4}-\d{2}(-\d{2})?$',
            r'^\d{4}/\d{2}(/\d{2})?$', r'^\d{4}\.\d{2}(\.\d{2})?$',
            r'^[Qq][1-4]$', r'^H[12]$', r'^\d{4}$', r'^\d{2}/\d{2}$',
            r'^\d{4}-\d{2}$']
    return any(re.match(p, text.strip()) for p in pats)

def is_axis_label(text):
    return is_number(text) or is_unit(text) or is_month_year(text)

def is_source_text(text):
    return any(kw in text for kw in ["资料来源", "数据来源", "来源：", "Source", "风险提示"])

def is_bullet_marker(text):
    return any(m in text for m in ["➢", "▶", "●", "■", "◆", "★", "▲", "▼", "·", "-", "•"])

def is_chart_title_prefix(text):
    return text.startswith("图：") or text.startswith("图:")

def extract_chart_title(text):
    if text.startswith("图："): return text[2:]
    if text.startswith("图:"): return text[2:]
    return text

def looks_like_legend(text):
    """Check if text looks like a chart legend/series name."""
    t = text.strip()
    if not t or len(t) > 80: return False
    if is_axis_label(t): return False
    if is_source_text(t): return False
    if is_bullet_marker(t): return False
    if re.match(r'^[\d一二三四五六七八九十]+[、.)）]', t): return False
    
    # Filter date/time axis labels
    date_pats = [r'^日\d+月\d+', r'^周\d+第', r'^第\d+周', r'^\d+日$',
                 r'^\d+/\d+', r'^\d+月\d+日', r'^月\d+', r'^年\d+',
                 r'^\d+年第', r'^第\d+周']
    for p in date_pats:
        if re.match(p, t): return False
    
    # Filter high-digit-ratio text
    digit_ratio = sum(1 for c in t if c.isdigit()) / max(len(t), 1)
    if digit_ratio > 0.4: return False
    
    # Filter repeated single-character patterns (like "日日日", "月月月")
    if re.match(r'^([\u4e00-\u9fff])\1{2,}$', t): return False
    # Filter text that's mostly the same character repeated
    if len(t) >= 3:
        char_counts = defaultdict(int)
        for c in t: char_counts[c] += 1
        max_rep = max(char_counts.values())
        if max_rep >= len(t) * 0.6: return False
    # Filter text containing many 日/月 characters (fragmented date labels)
    rm_count = sum(1 for c in t if c in "日月年月")
    if rm_count > len(t) * 0.5: return False
    # Filter text that looks like a paragraph (too long, has punctuation)
    if len(t) > 40: return False
    if t.count("，") + t.count("。") + t.count("；") > 1: return False
    # Filter text with mixed punctuation and numbers (paragraph text)
    punct_count = sum(1 for c in t if c in "，。；、（）()【】")
    if punct_count > 2 and len(t) > 10: return False
    
    # Filter single-character text (likely fragmented axis labels)
    if len(t) <= 1: return False
    
    # Has Chinese characters
    if re.search(r'[\u4e00-\u9fff]', t): return True
    
    # Short English abbreviation
    if re.match(r'^[A-Za-z]{1,10}$', t): return True
    
    return False

# ── Fuzzy match helper ──
def fuzzy_match(name1, name2):
    n1 = name1.lower().replace(" ", "").replace("（", "(").replace("）", ")")
    n2 = name2.lower().replace(" ", "").replace("（", "(").replace("）", ")")
    if n1 in n2 or n2 in n1: return True
    common = sum(1 for c in n1 if c in n2)
    return common >= max(3, min(len(n1), len(n2)) * 0.5)

# ── Merge fragmented words ──
def merge_nearby_words(words, x_tol=3, y_tol=4):
    """Merge nearby single-character words into meaningful text lines."""
    if not words: return []
    sorted_w = sorted(words, key=lambda w: (w['top'], w['x0']))
    merged = []
    current_line = []
    current_y = None
    
    for w in sorted_w:
        if current_y is None or abs(w['top'] - current_y) <= y_tol:
            if current_line:
                last = current_line[-1]
                if w['x0'] - last['x1'] <= x_tol:
                    current_line[-1] = {
                        'text': current_line[-1]['text'] + w['text'],
                        'x0': current_line[-1]['x0'], 'x1': w['x1'],
                        'top': current_line[-1]['top'],
                        'bottom': max(current_line[-1]['bottom'], w['bottom']),
                    }
                    continue
                else:
                    current_line.append(w)
            else:
                current_line.append(w)
        else:
            merged.extend(current_line)
            current_line = [w]
        current_y = w['top']
    merged.extend(current_line)
    return merged

# ── Chart region detection ──

def find_chart_regions_by_prefix(words, page_width, page_height):
    """Find chart regions using '图：' prefix."""
    chart_labels = []
    for wi, w in enumerate(words):
        if is_chart_title_prefix(w['text']):
            chart_labels.append(wi)
    
    if not chart_labels: return []
    
    # Group by row
    rows = []
    for wi in chart_labels:
        w = words[wi]
        cy = (w['top'] + w['bottom']) / 2
        matched = False
        for row in rows:
            if abs(row['cy'] - cy) < 30:
                row['indices'].append(wi)
                matched = True
                break
        if not matched:
            rows.append({'cy': cy, 'indices': [wi]})
    
    regions = []
    for row in rows:
        indices = sorted(row['indices'], key=lambda i: words[i]['x0'])
        for li, wi in enumerate(indices):
            w = words[wi]
            x_left = w['x0']
            x_right = words[indices[li+1]]['x0'] if li < len(indices)-1 else page_width
            y_top = w['top']
            y_bottom = page_height - 50
            for nr in rows:
                if nr['cy'] > row['cy'] + 30:
                    y_bottom = min(y_bottom, min(words[nwi]['top'] for nwi in nr['indices']) - 10)
                    break
            regions.append({
                'title': extract_chart_title(w['text']),
                'x_left': x_left, 'x_right': x_right,
                'y_top': y_top, 'y_bottom': y_bottom,
                'title_word': w, 'title_word_idx': wi,
            })
    return regions

def find_chart_regions_by_dsh(words, page_num, dsh_indicators, source_file, page_width, page_height):
    """Find chart regions using DSH data (for PDFs without '图：' prefix)."""
    page_indicators = []
    for ind in dsh_indicators:
        if ind.get("source_file", "") != source_file: continue
        ind_page = ind.get("page_num", "")
        if ind_page == str(page_num) or (ind_page and str(page_num) in ind_page.split(",")):
            name = ind.get("extracted_indicator_name", "")
            if name: page_indicators.append(name)
    
    if not page_indicators: return []
    
    regions = []
    used_words = set()
    
    for ind_name in page_indicators:
        best_match = None
        best_score = 0
        for wi, w in enumerate(words):
            if wi in used_words: continue
            text = w['text']
            if is_axis_label(text) or is_source_text(text) or is_chart_title_prefix(text): continue
            if len(text) <= 1: continue
            score = fuzzy_match(text, ind_name)
            if score:
                common = sum(1 for c in text.lower() if c in ind_name.lower())
                if common > best_score:
                    best_score = common
                    best_match = (wi, w, text)
        
        if best_match:
            wi, w, text = best_match
            used_words.add(wi)
            regions.append({
                'title': ind_name,
                'raw_title': text,
                'x_left': w['x0'], 'x_right': w['x1'],
                'y_top': w['top'], 'y_bottom': w['bottom'],
                'title_word': w, 'title_word_idx': wi,
            })
    
    # Expand regions
    if regions:
        sorted_r = sorted(regions, key=lambda r: r['x_left'])
        for i, region in enumerate(sorted_r):
            if i > 0:
                region['x_left'] = min(region['x_left'], sorted_r[i-1]['x_right'] + 5)
            if i < len(sorted_r) - 1:
                region['x_right'] = max(region['x_right'], sorted_r[i+1]['x_left'] - 5)
            else:
                region['x_right'] = page_width - 10
            region['y_top'] = max(0, region['y_top'] - 10)
            region['y_bottom'] = min(page_height - 30, region['y_bottom'] + 150)
    
    return regions

def collect_region_text(words, region):
    """Collect words within a chart region."""
    return [w for w in words
            if w['x0'] >= region['x_left'] - 5 and w['x1'] <= region['x_right'] + 5
            and w['top'] >= region['y_top'] - 5 and w['bottom'] <= region['y_bottom'] + 5]

def build_legend_list(region, region_words, title):
    """Build legend_list from chart region text."""
    legends = [title]
    for w in region_words:
        if w is region.get('title_word'): continue
        t = w['text']
        if looks_like_legend(t) and t not in legends:
            legends.append(t)
    return legends

def determine_plot_style(title, legend_list, region_words):
    """Determine plot style."""
    if any(kw in title for kw in ["截面", "饼", "占比", "分布", "构成", "结构"]):
        if len(legend_list) > 2: return "表格截面"
    if "季节" in title: return "季节图"
    
    has_dual = any(kw in title for kw in ["双轴", "双Y", "复合"])
    units_found = set()
    for w in region_words:
        if is_unit(w['text']): units_found.add(w['text'])
    
    if len(legend_list) > 2:
        if has_dual or len(units_found) > 1: return "双Y轴复合"
        return "多折线"
    return "单折线"

def determine_axis_info(title, region_words):
    """Determine axis info."""
    has_dual = any(kw in title for kw in ["双轴", "双Y", "复合"])
    units_found = set()
    unit_x = set()
    for w in region_words:
        if is_unit(w['text']):
            units_found.add(w['text'])
            unit_x.add(round(w['x0'] / 30) * 30)
    
    if has_dual or len(unit_x) > 1: return "双Y轴"
    if any('%' in w['text'] for w in region_words): return "单Y轴，含百分比轴"
    return "单Y轴"

def find_extracted_indicators(legend_list, dsh_indicators, source_file, page_num):
    """Find legend items that DSH successfully extracted.
    
    Returns legend items (not DSH names) that match DSH indicators.
    """
    # Build set of DSH indicator names for this source file
    dsh_names = set()
    for ind in dsh_indicators:
        if ind.get("source_file", "") != source_file: continue
        name = ind.get("extracted_indicator_name", "")
        if name: dsh_names.add(name)
    
    extracted = []
    for leg in legend_list:
        # Exact match first
        if leg in dsh_names:
            extracted.append(leg)
            continue
        # Fuzzy match against DSH names
        for dsh_name in dsh_names:
            if fuzzy_match(dsh_name, leg):
                extracted.append(leg)
                break
    return extracted

def build_note(plot_style, axis_info, legend_count, missing_count):
    parts = [f"绘图类型:{plot_style}", f"轴信息:{axis_info}", f"图例数:{legend_count}"]
    if legend_count > 1: parts.append(f"复合图({legend_count}图例)")
    if missing_count > 0: parts.append(f"漏提取{missing_count}项")
    return " | ".join(parts)

# ── Main chart parsing ──

def parse_pdf_charts(pdf_path, dsh_indicators):
    """Parse a PDF and extract chart-level metadata."""
    source_file = os.path.basename(pdf_path)
    charts = []
    chart_counter = 0
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            page_num = page_idx + 1
            raw_words = page.extract_words()
            if not raw_words: continue
            
            # Merge fragmented words
            words = merge_nearby_words(raw_words)
            page_width = page.width
            page_height = page.height
            
            # Try prefix method first
            regions = find_chart_regions_by_prefix(words, page_width, page_height)
            
            # Fallback to DSH method
            if not regions:
                regions = find_chart_regions_by_dsh(words, page_num, dsh_indicators, source_file, page_width, page_height)
            
            for region in regions:
                chart_counter += 1
                chart_local_id = f"chart_{chart_counter:02d}"
                chart_title = region['title']
                region_words = collect_region_text(words, region)
                legend_list = build_legend_list(region, region_words, chart_title)
                plot_style = determine_plot_style(chart_title, legend_list, region_words)
                axis_info = determine_axis_info(chart_title, region_words)
                extracted = find_extracted_indicators(legend_list, dsh_indicators, source_file, page_num)
                missing = [leg for leg in legend_list if leg not in extracted]
                note = build_note(plot_style, axis_info, len(legend_list), len(missing))
                
                charts.append({
                    "source_file": source_file,
                    "page_num": page_num,
                    "chart_local_id": chart_local_id,
                    "chart_title": chart_title,
                    "plot_style": plot_style,
                    "axis_info": axis_info,
                    "legend_list": legend_list,
                    "extracted_indicator_list": extracted,
                    "missing_in_legend": missing,
                    "note": note,
                })
    
    return charts

# ── Main ──

def main():
    log_f = open(LOG_FILE, 'w', encoding='utf-8')
    sys.stdout = log_f
    
    print("=" * 60)
    print("DSH-B_PDF_CHART_META_EXTRACT_TASK")
    print("=" * 60)
    
    manifest_data = load_manifest()
    dsh_indicators = load_dsh_extract()
    pdf_files = manifest_data.get("files", [])
    
    print(f"\nTotal PDFs: {len(pdf_files)}")
    print(f"DSH indicators: {len(dsh_indicators)}")
    
    all_charts = []
    for pf in pdf_files:
        pdf_path = pf["filepath"]
        fname = pf["filename"]
        print(f"\n[Parsing] {fname}")
        if not os.path.exists(pdf_path):
            print(f"   [WARN] Not found")
            continue
        charts = parse_pdf_charts(pdf_path, dsh_indicators)
        print(f"   [OK] {len(charts)} charts")
        if charts:
            lc = [len(c["legend_list"]) for c in charts]
            mc = [len(c["missing_in_legend"]) for c in charts]
            print(f"   Legend range: {min(lc)}-{max(lc)}")
            print(f"   Total missing: {sum(mc)}")
        all_charts.extend(charts)
    
    # Write CSV
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FN = ["source_file", "page_num", "chart_local_id", "chart_title",
          "plot_style", "axis_info", "legend_list",
          "extracted_indicator_list", "missing_in_legend", "note"]
    
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FN)
        w.writeheader()
        for c in all_charts:
            row = dict(c)
            for field in ["legend_list", "extracted_indicator_list", "missing_in_legend"]:
                if isinstance(row[field], list):
                    row[field] = " | ".join(row[field])
            w.writerow(row)
    print(f"\n[OK] CSV: {OUT_CSV}")
    print(f"   Total: {len(all_charts)} charts")
    
    # Write JSON
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "work_order": "DSH-B_PDF_CHART_META_EXTRACT_TASK",
            "description": "PDF chart metadata + legend extraction",
            "total_charts": len(all_charts),
            "charts": all_charts,
        }, f, ensure_ascii=False, indent=2)
    print(f"[OK] JSON: {OUT_JSON}")
    
    # Stats
    print("\n" + "=" * 60)
    print("[Stats]")
    print("=" * 60)
    
    sc = defaultdict(int)
    for c in all_charts: sc[c["source_file"]] += 1
    print("\nBy source file:")
    for sf, cnt in sorted(sc.items(), key=lambda x: -x[1]): print(f"  {sf}: {cnt}")
    
    pc = defaultdict(int)
    for c in all_charts: pc[c["plot_style"]] += 1
    print("\nBy plot style:")
    for style, cnt in sorted(pc.items(), key=lambda x: -x[1]): print(f"  {style}: {cnt}")
    
    lc = [len(c["legend_list"]) for c in all_charts]
    mc = [len(c["missing_in_legend"]) for c in all_charts]
    print(f"\nLegend stats:")
    print(f"  Charts: {len(all_charts)}")
    print(f"  Avg legends: {sum(lc)/len(lc):.1f}")
    print(f"  Max legends: {max(lc)}")
    print(f"  Min legends: {min(lc)}")
    print(f"  Total missing: {sum(mc)}")
    print(f"  Charts w/ missing: {sum(1 for m in mc if m > 0)}")
    
    print(f"\nTop 15 charts by legend count:")
    sc2 = sorted(all_charts, key=lambda c: -len(c["legend_list"]))
    for c in sc2[:15]:
        ls = " | ".join(c["legend_list"])[:100]
        ms = " | ".join(c["missing_in_legend"])[:60]
        print(f"  {c['source_file']} P{c['page_num']} {c['chart_local_id']}: {c['chart_title']}")
        print(f"    L: {ls}")
        print(f"    M: {ms if ms else 'none'}")
    
    print("\n[DONE]")
    log_f.close()
    return all_charts

if __name__ == "__main__":
    main()
