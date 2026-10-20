#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('STATUS.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

conflict_start = None
conflict_end = None
separator = None

for i, line in enumerate(lines):
    if line.startswith('<<<<<<< HEAD'):
        conflict_start = i
    elif line.startswith('=======') and conflict_start is not None and separator is None:
        separator = i
    elif line.startswith('>>>>>>> 9279a40'):
        conflict_end = i
        break

print(f'Conflict: lines {conflict_start+1}-{conflict_end+1}, separator at {separator+1}')

# HEAD section (lines between <<<<<<< HEAD and =======)
head_section = lines[conflict_start+1:separator]
# Theirs section (lines between ======= and >>>>>>> 9279a40)
theirs_section = lines[separator+1:conflict_end]

# Keep both sections: HEAD first, then theirs
resolved = lines[:conflict_start] + head_section + theirs_section + lines[conflict_end+1:]

with open('STATUS.md', 'w', encoding='utf-8') as f:
    f.writelines(resolved)

print('Conflict resolved: both HEAD and theirs sections preserved')
