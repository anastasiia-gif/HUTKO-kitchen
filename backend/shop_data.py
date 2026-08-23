"""
HUTKO — shop_data.py  (database-backed, with Excel safety fallback)

Public shop endpoints read products/bundles/settings from the DB with the
identical JSON shape the site already expects. Until the migration populates the
DB, it falls back to reading hutko_shop.xlsx so the shop is never empty.
"""

import os
import json
from flask import Blueprint, jsonify, request
from database import get_db

shop_bp = Blueprint('shop', __name__)

EXCEL_PATH = os.environ.get('SHOP_EXCEL_PATH', 'hutko_shop.xlsx')
_excel_cache = {}


def _db_count(table):
    conn = get_db()
    try:
        return conn.execute(f"SELECT COUNT(*) c FROM {table}").fetchone()['c']
    except Exception:
        return 0
    finally:
        conn.close()


def _excel_data():
    if not os.path.exists(EXCEL_PATH):
        return None
    try:
        from migrate_excel_to_db import parse_workbook
        mtime = os.path.getmtime(EXCEL_PATH)
        if _excel_cache.get('mtime') != mtime:
            _excel_cache['data'] = parse_workbook(EXCEL_PATH)
            _excel_cache['mtime'] = mtime
        return _excel_cache.get('data')
    except Exception as e:
        print(f"[SHOP] Excel fallback failed: {e}")
        return None


def _excel_product_public(p, variants):
    vs = [{'label': v['label'], 'price': v['price']} for v in variants if v.get('active', 1)]
    if not vs:
        vs = [{'label': p.get('unit', ''), 'price': p.get('base_price', 0)}]
    out = {k: p.get(k, '') for k in (
        'id', 'name_en', 'name_ua', 'name_nl', 'category',
        'desc_en', 'desc_ua', 'desc_nl', 'about_en', 'about_ua', 'about_nl',
        'prepare_en', 'prepare_ua', 'prepare_nl', 'ingredients_en', 'ingredients_ua', 'ingredients_nl',
        'hutko_tip_en', 'hutko_tip_ua', 'hutko_tip_nl', 'storage_en', 'storage_ua', 'storage_nl',
        'unit', 'badge', 'photo')}
    out['base_price'] = p.get('base_price', 0)
    out['gallery'] = p.get('gallery', []) or []
    out['dietary'] = p.get('dietary', []) or []
    out['variants'] = vs
    return out


def _json_list(raw):
    if not raw:
        return []
    try:
        val = json.loads(raw)
        if isinstance(val, list):
            return val
    except (ValueError, TypeError):
        return [x.strip() for x in str(raw).split(',') if x.strip()]
    return []


def _product_to_dict(row, variants_by_id):
    d = dict(row)
    pid = d['id']
    variants = variants_by_id.get(pid) or [{'label': d.get('unit') or '', 'price': d.get('base_price') or 0}]
    keys = ('name_en', 'name_ua', 'name_nl', 'category', 'desc_en', 'desc_ua', 'desc_nl',
            'about_en', 'about_ua', 'about_nl', 'prepare_en', 'prepare_ua', 'prepare_nl',
            'ingredients_en', 'ingredients_ua', 'ingredients_nl', 'hutko_tip_en', 'hutko_tip_ua',
            'hutko_tip_nl', 'storage_en', 'storage_ua', 'storage_nl', 'unit', 'badge', 'photo')
    out = {'id': pid}
    for k in keys:
        out[k] = d.get(k) or ''
    out['base_price'] = d.get('base_price') or 0
    out['gallery'] = _json_list(d.get('gallery'))
    out['dietary'] = _json_list(d.get('dietary'))
    out['variants'] = variants
    return out


def _bundle_to_dict(row):
    d = dict(row)
    return {
        'id': d['id'], 'name_en': d.get('name_en') or '', 'name_ua': d.get('name_ua') or '',
        'name_nl': d.get('name_nl') or '', 'size_label': d.get('size_label') or '',
        'items': _json_list(d.get('items')), 'original_price': d.get('original_price') or 0,
        'discount_price': d.get('discount_price') or 0, 'photo': d.get('photo') or '',
        'badge': d.get('badge') or '', 'choice_en': d.get('choice_en') or '',
        'choice_ua': d.get('choice_ua') or '', 'choice_nl': d.get('choice_nl') or '',
    }


def get_products(active_only=True):
    if _db_count('products') == 0:
        d = _excel_data()
        if not d:
            return []
        prods = [p for p in d['products'] if (not active_only or p.get('active', 1))]
        return [_excel_product_public(p, d['variants'].get(p['id'], [])) for p in prods]

    conn = get_db()
    where = "WHERE active=1" if active_only else ""
    prows = conn.execute(f"SELECT * FROM products {where} ORDER BY sort_order, name_en").fetchall()
    vrows = conn.execute("SELECT * FROM product_variants WHERE active=1 ORDER BY sort_order, id").fetchall()
    conn.close()
    variants_by_id = {}
    for v in vrows:
        variants_by_id.setdefault(v['product_id'], []).append({'label': v['label'] or '', 'price': v['price'] or 0})
    return [_product_to_dict(r, variants_by_id) for r in prows]


def get_bundles(active_only=True):
    if _db_count('bundles') == 0 and _db_count('products') == 0:
        d = _excel_data()
        if not d:
            return []
        out = []
        for b in d['bundles']:
            if active_only and not b.get('active', 1):
                continue
            out.append({
                'id': b['id'], 'name_en': b['name_en'], 'name_ua': b['name_ua'], 'name_nl': b['name_nl'],
                'size_label': b['size_label'], 'items': b['items'],
                'original_price': b['original_price'], 'discount_price': b['discount_price'],
                'photo': b['photo'], 'badge': b['badge'],
                'choice_en': b['choice_en'], 'choice_ua': b['choice_ua'], 'choice_nl': b['choice_nl'],
            })
        return out

    conn = get_db()
    where = "WHERE active=1" if active_only else ""
    rows = conn.execute(f"SELECT * FROM bundles {where} ORDER BY sort_order, name_en").fetchall()
    conn.close()
    return [_bundle_to_dict(r) for r in rows]


def get_settings_dict():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    if not rows:
        d = _excel_data()
        if d:
            return dict(d.get('settings', {}))
        return {}
    return {r['key']: (r['value'] or '') for r in rows}


@shop_bp.route('/api/shop/products', methods=['GET'])
def products():
    return jsonify({'products': get_products()}), 200


@shop_bp.route('/api/shop/bundles', methods=['GET'])
def bundles():
    return jsonify({'bundles': get_bundles()}), 200


@shop_bp.route('/api/shop/all', methods=['GET'])
def all_items():
    return jsonify({'products': get_products(), 'bundles': get_bundles()}), 200


@shop_bp.route('/api/shop/settings', methods=['GET'])
def settings():
    return jsonify({'settings': get_settings_dict()}), 200


@shop_bp.route('/api/shop/debug', methods=['GET'])
def debug():
    if request.headers.get('X-Admin-Password', '') != os.environ.get('ADMIN_PASSWORD', ''):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({
        'source': 'database' if _db_count('products') else 'excel-fallback',
        'products_count': _db_count('products'),
        'bundles_count': _db_count('bundles'),
        'settings_count': _db_count('settings'),
    }), 200
