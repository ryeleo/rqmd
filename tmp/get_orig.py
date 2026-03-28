import subprocess

# Get full content of workflows.py from HEAD
r = subprocess.run(['git', 'show', 'HEAD:src/rqmd/workflows.py'], 
                   capture_output=True, text=True,
                   cwd='/Users/rleonar7/git-repos/ac-cli')

if r.returncode == 0:
    content = r.stdout
    idx = content.find('def interactive_update_loop(')
    if idx >= 0:
        # Get 2000 chars starting from the function definition
        section = content[idx:idx+2000]
        with open('/Users/rleonar7/git-repos/ac-cli/tmp/orig_loop.txt', 'w') as f:
            f.write(section)
        print(f"Wrote {len(section)} chars to orig_loop.txt")
    else:
        print("NOT FOUND")
else:
    print("ERROR:", r.stderr[:100])
