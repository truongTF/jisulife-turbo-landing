#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Automated Price Synchronization Engine (update_prices.py)
Tự động đồng bộ và cập nhật giá bán các sản phẩm JISULIFE trên Landing Page:
 - Đọc & ghi file cấu hình prices.json
 - Đồng bộ song song vào mã HTML tĩnh của index.html (đảm bảo SEO & khi chưa tải JS)
 - Tùy chọn tự động commit và đẩy lên GitHub Pages (--push)
"""

import os
import re
import json
import argparse
from datetime import datetime
import subprocess


def format_vnd(amount):
    return f"{amount:,.0f}đ".replace(",", ".")


def update_prices(pro1s_price=None, life9_price=None, life7_price=None, push_to_github=False):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "prices.json")
    html_path = os.path.join(base_dir, "index.html")

    # 1. Load existing prices.json
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    changed = False
    if pro1s_price is not None and pro1s_price != data["products"]["pro1s"]["current_price"]:
        data["products"]["pro1s"]["current_price"] = int(pro1s_price)
        changed = True
    if life9_price is not None and life9_price != data["products"]["life9"]["current_price"]:
        data["products"]["life9"]["current_price"] = int(life9_price)
        changed = True
    if life7_price is not None and life7_price != data["products"]["life7"]["current_price"]:
        data["products"]["life7"]["current_price"] = int(life7_price)
        changed = True

    now = datetime.now()
    now_iso = now.isoformat()
    now_display = now.strftime("%d/%m/%Y")

    data["updated_at"] = now_iso
    data["updated_date_display"] = now_display

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[*] Đã cập nhật prices.json (Thời gian: {now_display})")
    for k, v in data["products"].items():
        print(f"  - {v['name']}: {format_vnd(v['current_price'])} (Gốc: {format_vnd(v['original_price'])})")

    # 2. Sync to index.html static fallbacks
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Update date display in pill
    html = re.sub(
        r'<strong id="priceSyncDateDisplay">.*?</strong>',
        f'<strong id="priceSyncDateDisplay">{now_display}</strong>',
        html,
    )

    # Update current prices in cards
    for key, prod in data["products"].items():
        formatted = format_vnd(prod["current_price"])
        html = re.sub(
            rf'<span class="price-current" data-price-key="{key}">.*?</span>',
            f'<span class="price-current" data-price-key="{key}">{formatted}</span>',
            html,
        )
        html = re.sub(
            rf'<td class="font-mono" style="color: var\(--accent-[a-z]+\); font-weight: 700;" data-compare-key="{key}">.*?</td>',
            lambda m, f=formatted, k=key: re.sub(r'>.*?<', f'>{f}<', m.group(0)),
            html,
        )

    # Update mobile bar min price
    min_p = min(p["current_price"] for p in data["products"].values())
    html = re.sub(
        r'<span class="mobile-bar-price" data-min-price>.*?</span>',
        f'<span class="mobile-bar-price" data-min-price>Từ {format_vnd(min_p)}</span>',
        html,
    )

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print("[*] Đã đồng bộ mã HTML tĩnh trong index.html")

    # 3. Optional Git commit & push
    if push_to_github:
        print("[*] Đang tự động commit và đẩy lên GitHub Pages...")
        subprocess.run(["git", "add", "prices.json", "index.html"], check=True)
        commit_msg = f"chore(price): auto-sync Shopee Mall prices ({now_display})"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("[+] Đã đẩy lên GitHub Pages thành công! Website sẽ cập nhật trực tuyến sau ~15 giây.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synchronize JISULIFE Product Prices")
    parser.add_argument("--pro1s", type=int, help="New price for Pro 1S in VND")
    parser.add_argument("--life9", type=int, help="New price for Life 9 in VND")
    parser.add_argument("--life7", type=int, help="New price for Life 7 in VND")
    parser.add_argument("--push", action="store_true", help="Automatically commit and push to GitHub Pages")
    args = parser.parse_args()

    update_prices(args.pro1s, args.life9, args.life7, args.push)
