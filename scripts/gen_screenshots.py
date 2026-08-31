#!/usr/bin/env python3
"""
截图所有页面，生成 screenshots/ 目录下的 PNG 文件。
供 export_selector.html 导出时加载预生成截图。
"""
import subprocess, os, json, time, sys

BASE = "/home/ubuntu/framework-tree"
SCREENSHOTS_DIR = os.path.join(BASE, "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# 加载映射表
node_map_path = os.path.join(BASE, "data", "export_node_map.json")
node_map = json.load(open(node_map_path))

# 收集所有页面
all_pages = set()
for pages in node_map.values():
    all_pages.update(pages)

all_pages = sorted(all_pages)
print(f"共 {len(all_pages)} 个页面需要截图")

# 截图
success = 0
failed = []

for i, page in enumerate(all_pages):
    url = f"http://127.0.0.1:8786/{page}"
    out_path = os.path.join(SCREENSHOTS_DIR, page.replace('.html', '.png'))
    
    # 跳过已存在的（增量更新）
    if os.path.exists(out_path):
        success += 1
        print(f"[{i+1}/{len(all_pages)}] 跳过（已存在）: {page}")
        continue
    
    print(f"[{i+1}/{len(all_pages)}] 截图: {page}")
    
    cmd = [
        'chromium-browser',
        '--headless',
        '--disable-gpu',
        '--no-sandbox',
        '--disable-dev-shm-usage',
        f'--screenshot={out_path}',
        '--window-size=2560,1440',
        '--hide-scrollbars',
        url
    ]
    
    try:
        result = subprocess.run(cmd, timeout=15, capture_output=True)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
            success += 1
        else:
            failed.append(page)
            if os.path.exists(out_path):
                os.remove(out_path)
    except Exception as e:
        failed.append(page)
        print(f"  ❌ 失败: {e}")
    
    time.sleep(0.5)  # 限频

print(f"\n✅ 成功: {success}/{len(all_pages)}")
if failed:
    print(f"❌ 失败: {len(failed)}")
    for p in failed[:10]:
        print(f"  - {p}")
    if len(failed) > 10:
        print(f"  ... 还有 {len(failed)-10} 个")
