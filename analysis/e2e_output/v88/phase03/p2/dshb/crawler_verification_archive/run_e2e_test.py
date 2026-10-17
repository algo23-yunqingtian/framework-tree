#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E2E integration test for P024"""
import sys, os, json, csv, logging, sqlite3, tempfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'crawler_archive'))
logging.basicConfig(level=logging.WARNING, format='%(message)s')

from db_interface import DatabaseInterface, SCHEMAS

SAMPLES = Path(os.path.join(os.path.dirname(__file__), '..', 'crawler_archive', 'samples'))

results = []
def test(name, condition, detail=''):
    status = 'PASS' if condition else 'FAIL'
    results.append((name, status, detail))
    print(f'  [{status}] {name} {detail}')

print('='*60)
print('T1: E2E INTEGRATION TEST')
print('='*60)

with tempfile.TemporaryDirectory() as tmpdir:
    db_path = Path(tmpdir) / 'test.db'
    db = DatabaseInterface(db_path)
    db.connect()
    test('DB: connect', db._connection is not None, '')

    csv_map = {
        'shfe_pbu_daily_kline_sample.csv': 'daily_kline',
        'shfe_znu_daily_kline_sample.csv': 'daily_kline',
        'dce_znu_daily_kline_sample.csv': 'daily_kline',
        'shfe_pbu_position_ranking_sample.csv': 'position_ranking',
        'shfe_znu_position_ranking_sample.csv': 'position_ranking',
        'shfe_pbu_warrant_registration_sample.csv': 'warrant_registration',
        'industry_lead_smelting_rate_sample.csv': 'industry_fundamental',
        'industry_zinc_smelting_rate_sample.csv': 'industry_fundamental',
    }

    for fname, table in csv_map.items():
        fpath = SAMPLES / fname
        if fpath.exists():
            n = db.load_csv(str(fpath), table)
            test(f'Load: {fname}', n >= 0, f'{n} rows into {table}')

    counts = db.get_table_counts()
    test('Table: daily_kline has data', counts['daily_kline'] > 0, f'count={counts["daily_kline"]}')
    test('Table: position_ranking has data', counts['position_ranking'] > 0, f'count={counts["position_ranking"]}')
    test('Table: warrant_registration has data', counts['warrant_registration'] > 0, f'count={counts["warrant_registration"]}')
    test('Table: industry_fundamental has data', counts['industry_fundamental'] > 0, f'count={counts["industry_fundamental"]}')

    print()
    print('--- IDEMPOTENCY TEST ---')
    for fname, table in csv_map.items():
        fpath = SAMPLES / fname
        if fpath.exists():
            n2 = db.load_csv(str(fpath), table)
            test(f'Idempotency: {fname}', n2 == 0, f'reload={n2} rows (expect 0)')

    counts2 = db.get_table_counts()
    test('Idempotency: counts unchanged', counts == counts2, f'before={counts} after={counts2}')

    rows = db.query_daily_kline('SHFE_PBU')
    test('Query: SHFE_PBU kline', len(rows) > 0, f'{len(rows)} rows')
    if rows:
        test('Query: date field', 'date' in rows[0], '')
        test('Query: close field', 'close' in rows[0], '')
        test('Query: symbol field', rows[0]['symbol'] == 'SHFE_PBU', f'symbol={rows[0]["symbol"]}')

    irows = db.query_industry_fundamental('LEAD_SMELTING_RATE')
    test('Query: industry LEAD_SMELTING_RATE', len(irows) > 0, f'{len(irows)} rows')

    integrity = db.verify_integrity()
    test('Integrity: OK', integrity['integrity_check'] == 'ok', f'status={integrity["integrity_check"]}')

    export_path = Path(tmpdir) / 'export.csv'
    n_exp = db.export_to_csv('daily_kline', str(export_path))
    test('Export: daily_kline', n_exp > 0, f'{n_exp} rows exported')
    test('Export: file exists', export_path.exists(), '')

    db.close()
    test('Close', db._connection is None, '')

passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')
print()
print('='*60)
print(f'TOTAL: {passed}/{len(results)} PASS, {failed}/{len(results)} FAIL')
print('='*60)
sys.exit(0 if failed == 0 else 1)