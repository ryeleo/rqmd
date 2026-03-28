"""Fix the remaining 3 else-blocks (with blank line) in workflows.py for INTERACTIVE-022."""
import ast

path = '/Users/rleonar7/git-repos/ac-cli/src/rqmd/workflows.py'
with open(path, encoding='utf-8') as f:
    content = f.read()

OLD_ELSE = '''        else:
            new_status = selected_value or str(requirement.get("status") or "")
            blocked_reason = prompt_for_blocked_reason() if "Blocked" in new_status else None
            deprecated_reason = prompt_for_deprecated_reason() if "Deprecated" in new_status else None

            changed = update_criterion_status(
                path,
                requirement,
                new_status,
                blocked_reason=blocked_reason,
                deprecated_reason=deprecated_reason,
            )'''

NEW_ELIF = '''        elif current_entry_field == "links":
            changed = prompt_for_links_flow(path, requirement, id_prefixes=id_prefixes)
        else:
            new_status = selected_value or str(requirement.get("status") or "")
            blocked_reason = prompt_for_blocked_reason() if "Blocked" in new_status else None
            deprecated_reason = prompt_for_deprecated_reason() if "Deprecated" in new_status else None

            changed = update_criterion_status(
                path,
                requirement,
                new_status,
                blocked_reason=blocked_reason,
                deprecated_reason=deprecated_reason,
            )'''

count = content.count(OLD_ELSE)
print(f"Found {count} instances of 8-space else branch (with blank line)")

if count != 3:
    print(f"ERROR: expected 3, got {count}")
    exit(1)

content = content.replace(OLD_ELSE, NEW_ELIF)
new_count = content.count('elif current_entry_field == "links":')
print(f"After replace, total links branches: {new_count}")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Wrote fixed file")

try:
    ast.parse(content)
    print("✓ Syntax OK!")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
    exit(1)
