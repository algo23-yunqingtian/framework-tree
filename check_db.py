#!/usr/bin/env python3
import sqlite3
conn = sqlite3.connect(r'scripts\api_cache.db')
cur = conn.cursor()
cur.execute("SELECT DISTINCT indicator_id FROM series_cache WHERE indicator_id_mapped != '' ORDER BY indicator_id LIMIT 30")
print('Mapped indicators in DB:')
for r in cur.fetchall():
    print(' ', r[0])
cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
print('Total unique indicators:', cur.fetchone()[0])
cur.execute("SELECT COUNT(DISTINCT indicator_id_mapped) FROM series_cache WHERE indicator_id_mapped != ''")
print('Unique mapped:', cur.fetchone()[0])
cur.execute("SELECT indicator_id_mapped, COUNT(DISTINCT indicator_id) FROM series_cache WHERE indicator_id_mapped != '' GROUP BY indicator_id_mapped")
print('\nMapped indicator counts:')
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]} DSHB indicators')
conn.close()
