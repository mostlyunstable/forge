import os
from pathlib import Path
from typing import List

class CommandSecurityPolicy:
    """
    Enforces security constraints on command execution.
    Independently validates executables, arguments, and paths.
    """
    
    ALLOWED_EXECUTABLES = {
        "ls": {"disallowed_flags": []},
        "cat": {"disallowed_flags": []},
        "pwd": {"disallowed_flags": []},
        "echo": {"disallowed_flags": []},
        "wc": {"disallowed_flags": []},
        "head": {"disallowed_flags": []},
        "tail": {"disallowed_flags": []},
        "sort": {"disallowed_flags": []},
        "uniq": {"disallowed_flags": []},
        "diff": {"disallowed_flags": []},
        "rg": {"disallowed_flags": []},
        "grep": {"disallowed_flags": []},
        # We explicitly remove 'find' due to -exec RCE risks, or we can carefully block -exec.
        "find": {"disallowed_flags": ["-exec", "-execdir", "-ok", "-okdir", "-delete"]},
        # 'git' allows executing hooks or path traversal via -C
        "git": {"disallowed_flags": ["-C", "--git-dir", "--work-tree", "--config"]},
        # python/uv/pytest have huge surface areas, but we allow them if paths are constrained.
        "python": {"disallowed_flags": ["-c", "-m"]},
        "python3": {"disallowed_flags": ["-c", "-m"]},
        "uv": {"disallowed_flags": []},
        "pytest": {"disallowed_flags": []}
    }

    @staticmethod
    def _is_path_like(arg: str) -> bool:
        """Heuristic to determine if an argument might be a path."""
        # It's a path if it contains a slash, or if it's explicitly navigating up,
        # or if it exists on disk relative to cwd. 
        # But since we can't be perfect, we must intercept ANY argument that contains '/' or '..'
        if "/" in arg or ".." in arg or str(arg).startswith("~") or arg == ".":
            return True
        # also if it looks like a file extension (e.g. .py, .txt)
        return False

    @classmethod
    def validate_and_sanitize(cls, tokens: List[str], base_dir: Path) -> List[str]:
        if not tokens:
            raise PermissionError("Empty command")

        executable_token = tokens[0]
        executable = os.path.basename(executable_token)
        if executable not in cls.ALLOWED_EXECUTABLES or "/" in executable_token or executable_token == "." or executable_token == "..":
            raise PermissionError(f"Executable '{executable_token}' is not allowed.")

        policy = cls.ALLOWED_EXECUTABLES[executable]
        
        # We process each argument
        for arg in tokens[1:]:
            # Check disallowed flags
            for flag in policy["disallowed_flags"]:
                if arg == flag or arg.startswith(flag + "="):
                    raise PermissionError(f"Flag '{flag}' is not allowed for executable '{executable}'.")

            # Check paths
            if cls._is_path_like(arg):
                # Try to resolve it
                # if it's an absolute path, we check if it's within base_dir
                # if it's relative, we check if it's within base_dir
                try:
                    # Treat it as a path relative to base_dir
                    resolved = (base_dir / arg).resolve()
                    resolved.relative_to(base_dir)
                except ValueError:
                    raise PermissionError(f"Argument '{arg}' resolves outside the allowed project directory.")

        return tokens
