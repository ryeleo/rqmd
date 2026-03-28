import subprocess
import sys
import sys

# Get git status
r = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], 
                   capture_output=True, text=True,
                   cwd='/Users/rleonar7/git-repos/ac-cli')
print("DIFF:", r.stdout.strip()[:200])

# Get git log
r2 = subprocess.run(['git', 'log', '--oneline', '-3'], 
                    capture_output=True, text=True,
                    cwd='/Users/rleonar7/git-repos/ac-cli')
print("LOG:", r2.stdout.strip()[:300])

# List stash
r3 = subprocess.run(['git', 'stash', 'list'], 
                    capture_output=True, text=True,
                    cwd='/Users/rleonar7/git-repos/ac-cli')
print("STASH:", r3.stdout.strip()[:200])

# Check if HEAD has workflows as unstaged (means git checkout would work)
r4 = subprocess.run(['git', 'show', 'HEAD:src/rqmd/workflows.py'], 
                    capture_output=True, text=True,
                    cwd='/Users/rleonar7/git-repos/ac-cli')
# Find the interactive_update_loop def in the original  
if r4.returncode == 0:
    content = r4.stdout
    idx = content.find('def interactive_update_loop(')
    if idx >= 0:
        print("FOUND def interactive_update_loop at char", idx)
        print("CONTEXT:", repr(content[idx:idx+400]))
    else:
        print("NOT FOUND in HEAD")
else:
    print("ERROR getting HEAD:", r4.stderr[:100])
