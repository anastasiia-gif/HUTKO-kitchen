"""
HUTKO — shop_data.py
Serves product and bundle data from hutko_shop.xlsx.
Frontend reads from /api/shop/products and /api/shop/bundles.
Admin can upload a new Excel via POST /api/admin/upload-excel.
"""

import os
import json
import traceback
from flask import Blueprint, jsonify, request
from openpyxl import load_workbook

shop_bp = Blueprint('shop', __name__)

EXCEL_PATH = os.environ.get('SHOP_EXCEL_PATH', 'hutko_shop.xlsx')
_cache = {}


def _load_excel():
    """Load and parse Excel file. Returns {products, bundles}."""
    if not os.path.exists(EXCEL_PATH):
        print(f"[SHOP] Excel not found at: {os.path.abspath(EXCEL_PATH)}")
        return {'products': [], 'bundles': []}

    try:
        wb = load_workbook(EXCEL_PATH, read_only=True, data_only=True)
    except Exception as e:
        print(f"[SHOP] Failed to open Excel: {e}")
        return {'products': [], 'bundles': []}

    print(f"[SHOP] Sheets found: {wb.sheetnames}")

    # ── PRODUCTS ──────────────────────────────────────────
    products = []
    if 'Products' in wb.sheetnames:
        ws = wb['Products']
        rows = list(ws.iter_rows(values_only=True))

        header_row = None
        for i, row in enumerate(rows):
            if row and row[1] == 'id':
                header_row = i
                break

        if header_row is not None:
            headers = [str(c).strip() if c else '' for c in rows[header_row][1:]]
            for row in rows[header_row + 1:]:
                vals = row[1:]
                if not any(vals):
                    continue
                d = dict(zip(headers, vals))
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
        print(f"[SHOP] Loaded {len(products)} products")

        # Parse variants (second table in same sheet - starts at row with 'product_id')
        variants_by_id = {}
        var_header_row = None
        for i, row in enumerate(rows):
            if row and row[1] == 'product_id':
                var_header_row = i
                break

        if var_header_row is not None:
            var_headers = [str(c).strip() if c else '' for c in rows[var_header_row][1:]]
            for row in rows[var_header_row + 1:]:
                vals = row[1:]
                if not any(vals):
                    continue
                d = dict(zip(var_headers, vals))
                pid = str(d.get('product_id', ''))
                if pid and str(d.get('active', 'yes')).lower() == 'yes':
                    variants_by_id.setdefault(pid, []).append({
                        'label': str(d.get('label', '')),
                        'price': float(d['price']) if d.get('price') else 0,
                    })

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
            if row and row[1] == 'id':
                header_row = i
                break

        if header_row is not None:
            headers = [str(c).strip() if c else '' for c in rows[header_row][1:]]
            for row in rows[header_row + 1:]:
                vals = row[1:]
                if not any(vals):
                    continue
                d = dict(zip(headers, vals))
                if d.get('id') and str(d.get('active', 'yes')).lower() == 'yes':
                    items = []
                    for part in str(d.get('items', '') or '').split(','):
                        part = part.strip()
                        if ':' in part:
                            pid, qty = part.split(':', 1)
                            try:
                                items.append({'product_id': pid.strip(), 'qty': int(qty.strip())})
                            except ValueError:
                                pass
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
        print(f"[SHOP] Loaded {len(bundles)} bundles")

    wb.close()
    return {'products': products, 'bundles': bundles}


def get_shop_data():
    """Return cached shop data, reload if Excel modified."""
    global _cache
    try:
        mtime = os.path.getmtime(EXCEL_PATH)
        if _cache.get('mtime') != mtime:
            print(f"[SHOP] Reloading Excel (mtime changed)")
            data = _load_excel()
            _cache = data
            _cache['mtime'] = mtime
    except FileNotFoundError:
        print(f"[SHOP] Excel file missing: {EXCEL_PATH}")
        if not _cache.get('products'):
            _cache = {'products': [], 'bundles': []}
    except Exception as e:
        print(f"[SHOP] Error loading Excel: {e}\n{traceback.format_exc()}")
        if not _cache.get('products'):
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


@shop_bp.route('/api/shop/debug', methods=['GET'])
def debug_excel():
    """Admin debug endpoint — shows Excel path and parse status."""
    admin_pw = request.headers.get('X-Admin-Password', '')
    if admin_pw != os.environ.get('ADMIN_PASSWORD', ''):
        return jsonify({'error': 'Unauthorized'}), 401
    data = get_shop_data()
    return jsonify({
        'excel_path':     os.path.abspath(EXCEL_PATH),
        'excel_exists':   os.path.exists(EXCEL_PATH),
        'products_count': len(data.get('products', [])),
        'bundles_count':  len(data.get('bundles', [])),
        'cached_mtime':   _cache.get('mtime'),
    }), 200


@shop_bp.route('/api/admin/upload-excel', methods=['POST'])
def upload_excel():
    """
    Replace the shop Excel file. Requires admin password in header.
    Usage: POST /api/admin/upload-excel
           Header: X-Admin-Password: <your password>
           Body: multipart/form-data with field 'file'
    """
    admin_pw = request.headers.get('X-Admin-Password', '')
    if admin_pw != os.environ.get('ADMIN_PASSWORD', ''):
        return jsonify({'error': 'Unauthorized'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded. Use field name "file".'}), 400

    f = request.files['file']
    if not f.filename.endswith('.xlsx'):
        return jsonify({'error': 'Only .xlsx files are accepted.'}), 400

    try:
        # Save to EXCEL_PATH, replacing old file
        f.save(EXCEL_PATH)
        # Force cache invalidation
        global _cache
        _cache = {}
        # Test parse immediately
        data = get_shop_data()
        return jsonify({
            'message':        'Excel uploaded and parsed successfully.',
            'products_count': len(data.get('products', [])),
            'bundles_count':  len(data.get('bundles', [])),
        }), 200
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500
