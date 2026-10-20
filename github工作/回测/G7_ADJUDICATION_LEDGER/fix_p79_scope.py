#!/usr/bin/env python3
"""Fix $script: prefix for variables used inside functions."""
import re

path = r"D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER\dshd_p79_a01_audit_watch.ps1"

with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Lines where function definitions start
lines = content.split('\n')
in_function = False
function_start = 0
function_indent = 0
fixed_count = 0

# Variables that need $script: prefix when used inside functions
target_vars = {
    '$trackingLog': '$script:trackingLog',
    '$artifactsDir': '$script:artifactsDir',
    '$baseDir': '$script:baseDir',
    '$outputSampleDir': '$script:outputSampleDir',
    '$monitorPid': '$script:monitorPid',
    '$state': '$script:state',
}

new_lines = []
for i, line in enumerate(lines):
    stripped = line.strip()
    
    # Detect function definition start
    if stripped.startswith('function '):
        in_function = True
        function_start = i
        # Get the indent level of the function definition
        func_indent_str = line[:len(line) - len(line.lstrip())]
        function_indent = len(func_indent_str)
        new_lines.append(line)
        continue
    
    # Detect end of function (brace at same or lower indent as function)
    if in_function and stripped == '}':
        # Check if this brace is at the function's indent level
        brace_indent = len(line) - len(line.lstrip())
        if brace_indent <= function_indent:
            in_function = False
        new_lines.append(line)
        continue
    
    # If inside a function, replace target variables
    if in_function:
        for old, new in target_vars.items():
            # Only replace if not already prefixed
            # Skip lines that define the variable (assignment)
            # Skip lines where the variable is on the left side of assignment
            # Skip lines that are variable definitions at the top of the function
            # Skip lines like "$state = @{" (definition)
            if old == '$state' and re.match(r'\s*\$state\s*=', line):
                continue  # Don't replace the definition
            if old == '$state' and re.match(r'\s*\$state\.', line):
                # This is accessing properties of $state, replace
                line = line.replace(old, new)
                fixed_count += 1
                continue
            
            # Replace in all other contexts
            # But skip if already has $script: prefix
            if old in line and new not in line and (old + ' ' in line or old + '.' in line or old + ')' in line or old + ',' in line or old + ';' in line or old + '}' in line or old + ']