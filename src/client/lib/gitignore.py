#VIBECODED WHOLE
from subprocess import run
def is_gitignored(base_path, relative_path): return run(["git", "check-ignore", "-q", "--", relative_path], cwd=base_path).returncode == 0
#VIBECODED WHOLE
