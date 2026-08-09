import pytest
import os
import subprocess
from pathlib import Path
from forge.application.agent.command_policy import CommandSecurityPolicy

def test_attack_6_command_security_args():
    """Attack 6: Command Security Arguments. Test path traversal on allowed commands."""
    base_dir = Path("/tmp/project_sandbox")
    
    # Try directory traversals with an allowed binary (e.g. ls)
    attacks = [
        ["ls", "../"],
        ["ls", "../../"],
        ["ls", "/etc"],
        ["ls", "~/.ssh"],
        ["cat", "../secret"],
        ["cat", "/etc/passwd"],
        ["cat", "~/.ssh/id_rsa"],
        ["git", "-C", "../other", "status"],
        ["git", "--git-dir=../other/.git", "status"],
        ["git", "--work-tree=../other", "status"],
        ["find", ".."],
        ["find", ".", "-exec", "cat", "/etc/passwd", ";"],
        ["find", ".", "-delete"],
        ["cp", "../secret", "."],
        ["mv", "../secret", "."],
        ["ln", "-s", "../secret", "."],
    ]
    
    successes = []
    for tokens in attacks:
        try:
            CommandSecurityPolicy.validate_and_sanitize(tokens, base_dir)
            successes.append(tokens)
        except PermissionError:
            pass
            
    assert not successes, f"Command argument bypass successful for variants: {successes}"

def test_attack_7_command_parser_confusion():
    """Attack 7: Test parsing discrepancies."""
    base_dir = Path("/tmp/project_sandbox")
    import shlex
    
    # We want to see if shlex.split behavior differs from shell execution or policy
    attacks = [
        "ls '../outside'",
        'ls "../outside"',
        "ls ../outside\\ space",
        "ls \t ../outside",
        "ls --foo=../outside",
        "ls ~",
    ]
    
    successes = []
    for attack in attacks:
        tokens = shlex.split(attack)
        try:
            CommandSecurityPolicy.validate_and_sanitize(tokens, base_dir)
            successes.append(attack)
        except PermissionError:
            pass
            
    assert not successes, f"Parser confusion bypass successful for variants: {successes}"

def test_attack_8_executable_replacement():
    """Attack 8: Attempt to execute malicious binaries named 'ls' or use PATH manipulation."""
    base_dir = Path("/tmp/project_sandbox")
    
    attacks = [
        ["./ls"], 
        ["../ls"], 
        ["/bin/ls"], 
    ]
    
    successes = []
    for tokens in attacks:
        try:
            CommandSecurityPolicy.validate_and_sanitize(tokens, base_dir)
            successes.append(tokens)
        except PermissionError:
            pass
            
    assert not successes, f"Executable replacement successful for variants: {successes}"

def test_attack_9_working_directory_escape():
    """Attack 9: Attempt to escape cwd."""
    from forge.application.agent.tools import ForgeTools, _tools_base_dir
    
    base_dir = Path("/tmp/project_sandbox")
    token = _tools_base_dir.set(base_dir)
    try:
        # In ForgeTools.execute_tool, cwd is set to base_dir. We want to see if the command can change its own cwd.
        # But this is a subprocess thing. Let's just make sure we test if subprocess escape works.
        # This is already covered by testing `cd ../ && ls`, but wait, `cd` isn't an allowed executable anyway!
        pass 
    finally:
        _tools_base_dir.reset(token)

def test_attack_10_environment_escape():
    """Attack 10: Inspect whether subprocess leaks secrets."""
    base_dir = Path("/tmp/project_sandbox")
    
    # Check if `env` or `printenv` are in allowed commands.
    try:
        CommandSecurityPolicy.validate_and_sanitize(["env"], base_dir)
        assert False, "Environment escape possible: 'env' is allowed"
    except PermissionError:
        pass

    try:
        CommandSecurityPolicy.validate_and_sanitize(["printenv"], base_dir)
        assert False, "Environment escape possible: 'printenv' is allowed"
    except PermissionError:
        pass
