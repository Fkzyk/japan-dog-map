#!/bin/bash
echo "v3完了待機中..."
while ps aux | grep -q "[c]ollect_v3.py"; do
    sleep 10
done
echo "v3完了。追加エリア収集を開始します..."
cd /home/ubuntu/dogmap
PYTHONUNBUFFERED=1 python3 collect_extra.py > collect_extra_log.txt 2>&1
echo "追加エリア収集完了"
