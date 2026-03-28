"""Restore workflows.py from HEAD and apply the correct minimal changes for INTERACTIVE-022."""
import subprocess

# Step 1: Get the HEAD version
r = subprocess.run(['git', 'show', 'HEAD:src/rqmd/workflows.py'], 
                   capture_output=True, text=True,
                   cwd='/Users/rleonar7/git-repos/ac-cli')

if r.returncode != 0:
    print("ERROR getting HEAD:", r.stderr[:200])
    exit(1)

content = r.stdout
print(f"Got HEAD content: {len(content)} chars")

# Step 2: Apply changes
# 2a. Update import
old_import = "from .status_update import (print_criterion_panel, prompt_for_blocked_reason,\n                            prompt_for_deprecated_reason,"
new_import = "from .status_update import (print_criterion_panel, prompt_for_blocked_reason,\n                            prompt_for_deprecated_reason, prompt_for_links_flow,"
assert old_import in content, f"OLD IMPORT not found"
content = content.replace(old_import, new_import, 1)
print("✓ Updated import")

# 2b. Update ENTRY_FIELDS
old_fields = 'ENTRY_FIELDS = ("status", "priority", "flagged")'
new_fields = 'ENTRY_FIELDS = ("status", "priority", "flagged", "links")'
assert old_fields in content, "ENTRY_FIELDS not found"
content = content.replace(old_fields, new_fields, 1)
print("✓ Updated ENTRY_FIELDS")

# 2c. Add links branch to _build_requirement_field_menu
old_menu = '''    if active_field == "priority":
        labels = [label for label, _ in PRIORITY_ORDER]
        options = [style_priority_label(label) for label in labels]
        current_value = str(requirement.get("priority") or "")
        try:
            current_index = labels.index(current_value)
        except ValueError:
            current_index = None
        highlight_bg = _priority_highlight_bg(current_value)
        title = f"Set priority for {requirement['id']}{title_suffix}\\nsetting: priority"
        return title, labels, options, current_index, highlight_bg

    labels = [label for label, _ in STATUS_ORDER]'''
new_menu = '''    if active_field == "priority":
        labels = [label for label, _ in PRIORITY_ORDER]
        options = [style_priority_label(label) for label in labels]
        current_value = str(requirement.get("priority") or "")
        try:
            current_index = labels.index(current_value)
        except ValueError:
            current_index = None
        highlight_bg = _priority_highlight_bg(current_value)
        title = f"Set priority for {requirement['id']}{title_suffix}\\nsetting: priority"
        return title, labels, options, current_index, highlight_bg

    if active_field == "links":
        existing_links = requirement.get("links") or []
        link_count = len(existing_links)  # type: ignore[arg-type]
        count_str = f"{link_count} link{\'s\' if link_count != 1 else \'\'}" if link_count else "no links"
        labels = ["manage"]
        options = [f"🔗 Manage links ({count_str})\\u2026"]
        title = f"Edit links for {requirement[\'id\']}{title_suffix}\\nsetting: links"
        return title, labels, options, None, "\\x1b[48;5;25m"

    labels = [label for label, _ in STATUS_ORDER]'''
assert old_menu in content, "MENU BRANCH not found"
content = content.replace(old_menu, new_menu, 1)
print("✓ Added links menu branch")

# 2d. Add links branch to each of the 5 field-handling elif blocks
# Each looks like:
#         elif current_entry_field == "flagged":
#             changed = update_criterion_status(
#                 path,
#                 requirement,
#                 str(requirement.get("status") or ""),
#                 new_flagged=(selected_value == "true"),
#             )
#         else:
#             new_status = selected_value ...

LINKS_BRANCH = '''        elif current_entry_field == "links":
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

# The old else branch (8-space indent) that we're replacing (careful: exact text)
OLD_ELSE_8 = '''        else:
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

count_8 = content.count(OLD_ELSE_8)
print(f"Found {count_8} instances of 8-space else branch")

content = content.replace(OLD_ELSE_8, LINKS_BRANCH)
new_count = content.count(LINKS_BRANCH)
print(f"After replace, found {new_count} instances of links branch")

# Also handle interactive_update_loop which has 12-space for selected_path/selected_criterion
# and separate process_file calls for each branch
LINKS_BRANCH_12 = '''            elif current_entry_field == "links":
                changed = prompt_for_links_flow(
                    selected_path,
                    selected_criterion,
                    id_prefixes=id_prefixes,
                )
                process_file(
                    selected_path,
                    check_only=False,
                    include_status_emojis=include_status_emojis,
                    include_priority_summary=include_priority_summary,
                )
            else:
                new_status = selected_value or str(selected_criterion.get("status") or "")
                blocked_reason = prompt_for_blocked_reason() if "Blocked" in new_status else None
                deprecated_reason = prompt_for_deprecated_reason() if "Deprecated" in new_status else None

                changed = update_criterion_status(
                    selected_path,
                    selected_criterion,
                    new_status,
                    blocked_reason=blocked_reason,
                    deprecated_reason=deprecated_reason,
                )
                process_file(
                    selected_path,
                    check_only=False,
                    include_status_emojis=include_status_emojis,
                    include_priority_summary=include_priority_summary,
                )'''

OLD_ELSE_12 = '''            else:
                new_status = selected_value or str(selected_criterion.get("status") or "")
                blocked_reason = prompt_for_blocked_reason() if "Blocked" in new_status else None
                deprecated_reason = prompt_for_deprecated_reason() if "Deprecated" in new_status else None

                changed = update_criterion_status(
                    selected_path,
                    selected_criterion,
                    new_status,
                    blocked_reason=blocked_reason,
                    deprecated_reason=deprecated_reason,
                )
                process_file(
                    selected_path,
                    check_only=False,
                    include_status_emojis=include_status_emojis,
                    include_priority_summary=include_priority_summary,
                )'''

count_12 = content.count(OLD_ELSE_12)
print(f"Found {count_12} instances of 12-space selected_criterion else branch")
if count_12 > 0:
    content = content.replace(OLD_ELSE_12, LINKS_BRANCH_12, 1)
    print("✓ Updated 12-space (selected_criterion) branch")
else:
    print("WARNING: 12-space else branch not found")

# Write the result
with open('/Users/rleonar7/git-repos/ac-cli/src/rqmd/workflows.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nWrote fixed file: {len(content)} chars")

# Verify syntax
import ast
try:
    ast.parse(content)
    print("✓ Syntax OK!")
except SyntaxError as e:
    print(f"✗ SYNTAX ERROR: {e}")
