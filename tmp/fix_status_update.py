"""Dedent the 3 link-management functions that were accidentally nested inside prompt_for_priority."""
import ast

path = '/Users/rleonar7/git-repos/ac-cli/src/rqmd/status_update.py'
with open(path, encoding='utf-8') as f:
    lines = f.readlines()

# Find start and end of the misindented block
start = None
end = None
for i, line in enumerate(lines):
    if line == '    def _add_link_to_file(path: Path, requirement: dict, link_text: str) -> None:\n':
        start = i
    if start is not None and line == 'def apply_status_change_by_id(\n':
        end = i
        break

if start is None or end is None:
    print(f"ERROR: Could not find markers (start={start}, end={end})")
    exit(1)

print(f"Misindented block: lines {start+1} to {end} (0-indexed {start} to {end-1})")

# Dedent the block by 4 spaces
fixed_lines = []
for i, line in enumerate(lines):
    if start <= i < end:
        if line.startswith('    '):
            fixed_lines.append(line[4:])
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

content = ''.join(fixed_lines)
try:
    ast.parse(content)
    print("✓ Syntax OK!")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
    exit(1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Wrote fixed file")
