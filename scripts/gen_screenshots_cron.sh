#!/bin/bash
# 每周截图更新 cron（周日 18:00）
# 用法: crontab -e 加一行: 0 18 * * 0 /home/ubuntu/framework-tree/scripts/gen_screenshots_cron.sh

cd /home/ubuntu/framework-tree

# 1. 重建映射表
python3 scripts/gen_export_node_map.py

# 2. 截图
python3 scripts/gen_screenshots.py

# 3. 推到 GitHub（如果有变更）
git add data/export_node_map.json screenshots/
if git diff --cached --quiet; then
    echo "无变更"
else
    git commit -m "[B] 更新截图 $(date +%F)"
    GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
fi
