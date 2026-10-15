#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('framework-tree/analysis/e2e_output/v88/phase03/p0/phase03_test.db')
cur = conn.cursor()

# Check lithium-related indicators
cur.execute("""
    SELECT indicator_id, indicator_id_mapped, commodity, COUNT(*) as cnt 
    FROM series_cache WHERE commodity='li' 
    GROUP BY indicator_id, indicator_id_mapped, commodity ORDER BY indicator_id
""")
print('=== Lithium indicators in DB ===')
for r in cur.fetchall():
    print(f'  {r[0]:<35} -> {str(r[1]):<25} comm={r[2]} rows={r[3]}')

# Check silicon-related indicators
cur.execute("""
    SELECT indicator_id, indicator_id_mapped, commodity, COUNT(*) as cnt 
    FROM series_cache WHERE commodity='si' 
    GROUP BY indicator_id, indicator_id_mapped, commodity ORDER BY indicator_id
""")
print('\n=== Silicon indicators in DB ===')
for r in cur.fetchall():
    print(f'  {r[0]:<35} -> {str(r[1]):<25} comm={r[2]} rows={r[3]}')

# Check COMEX indicators
cur.execute("""
    SELECT indicator_id, indicator_id_mapped, commodity, COUNT(*) as cnt 
    FROM series_cache WHERE indicator_id LIKE '%comex%' OR indicator_id_mapped LIKE '%COMEX%' 
    GROUP BY indicator_id, indicator_id_mapped, commodity
""")
print('\n=== COMEX indicators in DB ===')
for r in cur.fetchall():
    print(f'  {r[0]:<35} -> {str(r[1]):<25} comm={r[2]} rows={r[3]}')

# Check TOP20 indicators
cur.execute("""
    SELECT indicator_id, indicator_id_mapped, commodity, COUNT(*) as cnt 
    FROM series_cache WHERE indicator_id LIKE '%top20%' OR indicator_id_mapped LIKE '%TOP20%' 
    GROUP BY indicator_id, indicator_id_mapped, commodity
""")
print('\n=== TOP20 indicators in DB ===')
for r in cur.fetchall():
    print(f'  {r[0]:<35} -> {str(r[1]):<25} comm={r[2]} rows={r[3]}')

# Check SPOT indicators
cur.execute("""
    SELECT indicator_id, indicator_id_mapped, commodity, COUNT(*) as cnt 
    FROM series_cache WHERE indicator_id LIKE '%spot%' OR indicator_id_mapped LIKE '%SPOT%' 
    GROUP BY indicator_id, indicator_id_mapped, commodity
""")
print('\n=== SPOT indicators in DB ===')
for r in cur.fetchall():
    print(f'  {r[0]:<35} -> {str(r[1]):<25} comm={r[2]} rows={r[3]}')

# Check CU_BALANCE_SHEET or similar
cur.execute("""
    SELECT indicator_id, indicator_id_mapped, commodity, COUNT(*) as cnt 
    FROM series_cache WHERE indicator_id LIKE '%balance%' OR indicator_id_mapped LIKE '%BALANCE%' 
    GROUP BY indicator_id, indicator_id_mapped, commodity
""")
print('\n=== BALANCE indicators in DB ===')
for r in cur.fetchall():
    print(f'  {r[0]:<35} -> {str(r[1]):<25} comm={r[2]} rows={r[3]}')

# Total distinct indicator_id_mapped values
cur.execute("SELECT COUNT(DISTINCT indicator_id_mapped) FROM series_cache WHERE indicator_id_mapped IS NOT NULL")
print(f'\nTotal distinct indicator_id_mapped: {cur.fetchone()[0]}')

# Count indicators with source=derived
cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache WHERE source='derived'")
print(f'Distinct derived indicators: {cur.fetchone()[0]}')

conn.close()