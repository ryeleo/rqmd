import subprocess

# Get full content of workflows.py from HEAD
r = subprocess.run(['git', 'show', 'HEAD:src/rqmd/workflows.py'], 
                   capture_output=True, text=True,
                   cwd='/Users/rleonar7/git-repos/ac-cli')

if r.returncode == 0:
    content = r.stdout
    idx = content.find('def interactive_update_loop(')
    if idx >= 0:
        # Get 4000 chars starting from the function definition
        section = content[idx:idx+4000]
        with open('/Users/rleonar7/git-repos/ac-cli/tmp/orig_loop2.txt', 'w') as f:
            f.write(section)
        print(f"Wrote {len(section)} chars to orig_loop2.txt")
    
    # Also get the focused_target end (2000 chars before the function)
    section2 = content[max(0, idx-500):idx]
    with open('/Users/rleonar7/git-repos/ac-cli/tmp/orig_before.txt', 'w') as f:
        f.write(section2)
    print(f"Wrote {len(section2)} chars to orig_before.txt")
else:
    print("ERROR:", r.stderr[:100])
