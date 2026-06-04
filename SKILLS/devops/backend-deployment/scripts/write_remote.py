#!/usr/bin/env python3
"""Safe remote file writer — avoids heredoc quoting issues over SSH.

Usage:
    python3 write_remote.py <ssh_args...> <remote_path> <content>

Example:
    python3 write_remote.py -i ~/.ssh/id_ed25519 user@host /path/to/file.py "print('hello')"
"""
import subprocess
import sys

def main():
    args = sys.argv[1:]
    if len(args) < 3:
        print("Usage: write_remote.py <ssh_args> <remote_path> <content>")
        sys.exit(1)

    # Last arg is content, second-to-last is path, rest are ssh args
    content = args[-1]
    remote_path = args[-2]
    ssh_args = args[:-2]

    cmd = ["ssh"] + ssh_args + [f"python3 -c \"import pathlib; pathlib.Path('{remote_path}').write_text('''{content}''')\""]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"Written to {remote_path}")

if __name__ == "__main__":
    main()
