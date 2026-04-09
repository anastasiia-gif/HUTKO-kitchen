"""
HUTKO — shop_data.py
Serves product and bundle data from hutko_shop.xlsx.
Frontend reads from /api/shop/products and /api/shop/bundles.
"""

import os
import json
from flask import Blueprint, jsonify
from openpyxl import load_workbook

shop_bp = Blueprint('shop', __name__)

EXCEL_PATH = os.environ.get('SHOP_EXCEL_PATH', 'hutko_shop.xlsx')
_cache = {}


def _load_excel():
    """Load and parse Excel file. Returns {products, bundles}."""
    if not os.path.exists(EXCEL_PATH):
        return {'products': [], 'bundles': []}

    wb = load_workbook(EXCEL_PATH, read_only=True, data_only=True)

    # ── PRODUCTS ──────────────────────────────────────────
    products = []
    if 'Products' in wb.sheetnames:
        ws = wb['Products']
        rows = list(ws.iter_rows(values_only=True))

        # Find header row (row with 'id' in col B = index 1)
        header_row = None
        for i, row in enumerate(rows):
            if row[1] == 'id':
                header_row = i
                break

        if header_row is not None:
            headers = [str(c).strip() if c else '' for c in rows[header_row][1:]]
            for row in rows[header_row + 1:]:
                vals = row[1:]
                if not any(vals):
                    continue
                d = {}
                for h, v in zip(headers, vals):
                    d[h] = v
                if d.get('id') and str(d.get('active', 'yes')).lower() == 'yes':
                    products.append({
                        'id':          str(d.get('id', '')),
                        'name_en':     str(d.get('name_en', '')),
                        'name_ua':     str(d.get('name_ua', '')),
                        'name_nl':     str(d.get('name_nl', '')),
                        'category':    str(d.get('category', '')),
                        'desc_en':     str(d.get('description_en', '')),
                        'desc_ua':     str(d.get('description_ua', '')),
                        'desc_nl':     str(d.get('description_nl', '')),
                        'base_price':  float(d['base_price']) if d.get('base_price') else 0,
                        'unit':        str(d.get('unit', '')),
                        'badge':       str(d.get('badge', '') or ''),
                        'photo':       str(d.get('photo_file', '')),
                        'dietary':     [t.strip() for t in str(d.get('dietary', '') or '').split(',') if t.strip()],
                    })

        # Parse variants (second table in same sheet - starts at row with 'product_id')
        variants_by_id = {}
        var_header_row = None
        for i, row in enumerate(rows):
            if row[1] == 'product_id':
                var_header_row = i
                break

        if var_header_row is not None:
            var_headers = [str(c).strip() if c else '' for c in rows[var_header_row][1:]]
            for row in rows[var_header_row + 1:]:
                vals = row[1:]
                if not any(vals):
                    continue
                d = {}
                for h, v in zip(var_headers, vals):
                    d[h] = v
                pid = str(d.get('product_id', ''))
                if pid and str(d.get('active', 'yes')).lower() == 'yes':
                    if pid not in variants_by_id:
                        variants_by_id[pid] = []
                    variants_by_id[pid].append({
                        'label': str(d.get('label', '')),
                        'price': float(d['price']) if d.get('price') else 0,
                    })

        # Attach variants to products
        for p in products:
            p['variants'] = variants_by_id.get(p['id'], [
                {'label': p['unit'], 'price': p['base_price']}
            ])

    # ── BUNDLES ───────────────────────────────────────────
    bundles = []
    if 'Bundles' in wb.sheetnames:
        ws = wb['Bundles']
        rows = list(ws.iter_rows(values_only=True))

        header_row = None
        for i, row in enumerate(rows):
            if row[1] == 'id':
                header_row = i
                break

        if header_row is not None:
            headers = [str(c).strip() if c else '' for c in rows[header_row][1:]]
            for row in rows[header_row + 1:]:
                vals = row[1:]
                if not any(vals):
                    continue
                d = {}
                for h, v in zip(headers, vals):
                    d[h] = v
                if d.get('id') and str(d.get('active', 'yes')).lower() == 'yes':
                    # Parse items: "syrnyky:8,borscht:1"
                    items = []
                    for part in str(d.get('items', '') or '').split(','):
                        part = part.strip()
                        if ':' in part:
                            pid, qty = part.split(':', 1)
                            items.append({'product_id': pid.strip(), 'qty': int(qty.strip())})

                    bundles.append({
                        'id':             str(d.get('id', '')),
                        'name_en':        str(d.get('name_en', '')),
                        'name_ua':        str(d.get('name_ua', '')),
                        'name_nl':        str(d.get('name_nl', '')),
                        'size_label':     str(d.get('size_label', '')),
                        'items':          items,
                        'original_price': float(d['original_price']) if d.get('original_price') else 0,
                        'discount_price': float(d['discount_price']) if d.get('discount_price') else 0,
                        'photo':          str(d.get('photo_file', '')),
                        'badge':          str(d.get('badge', '') or ''),
                    })

    wb.close()
    return {'products': products, 'bundles': bundles}


def get_shop_data():
    """Return cached shop data, reload if Excel modified."""
    global _cache
    try:
        mtime = os.path.getmtime(EXCEL_PATH)
        if _cache.get('mtime') != mtime:
            _cache = _load_excel()
            _cache['mtime'] = mtime
    except Exception as e:
        print(f'[SHOP] Error loading Excel: {e}')
        if not _cache:
            _cache = {'products': [], 'bundles': []}
    return _cache


@shop_bp.route('/api/shop/products', methods=['GET'])
def get_products():
    data = get_shop_data()
    return jsonify({'products': data.get('products', [])}), 200


@shop_bp.route('/api/shop/bundles', methods=['GET'])
def get_bundles():
    data = get_shop_data()
    return jsonify({'bundles': data.get('bundles', [])}), 200


@shop_bp.route('/api/shop/all', methods=['GET'])
def get_all():
    data = get_shop_data()
    return jsonify({
        'products': data.get('products', []),
        'bundles':  data.get('bundles', []),
    }), 200
