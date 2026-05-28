# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
import atexit
import os
import re
import shutil
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from _pytest.config import Config
from pytest import TempPathFactory
from rich import box, print
from rich.console import Console
from rich.table import Table

from src.helper_lib import find_git_root, get_github_base_url

"""
This script's main usecase is to test consumers of Docs-As-Code with
the new changes made in PR's.
This enables us to find new issues and problems we introduce with changes
that we otherwise would only know much later.
There are several things to note.

- The `print` function has been overwritten by the 'rich' package to allow for richer
text output.
- The script itself takes quiet a bit of time, roughly 5+ min for a full run.
- If you need more output, enable it via `-v` or `-vv`
- Start the script via the following command:
    - bazel run //:ide_support
    - .venv_docs/bin/python -m pytest -s src/tests
    (If you need more verbosity add `-v` or `-vv`)
"""

# Max width of the printout
# Trial and error has shown that 80 the best value is for GH CI output
len_max = 120
CACHE_DIR = Path.home() / ".cache" / "docs_as_code_consumer_tests"
log_file_name = "consumer_test.log"
# Need to ignore the ruff error here. Due to how the script is written,
# can not use a context manager to open the log file, even though it would be preferable
# In a future re-write this should be considered.
log_fp = open(log_file_name, "a", encoding="utf-8")  # noqa: SIM115
atexit.register(log_fp.close)
console = Console(file=log_fp, force_terminal=False, width=120, color_system=None)


@dataclass
class ConsumerRepo:
    name: str
    git_url: str
    commands: list[str]
    test_commands: list[str]


@dataclass
class BuildOutput:
    returncode: int
    stdout: str
    stderr: str
    warnings: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class Result:
    repo: str
    cmd: str
    local_or_git: str
    passed: bool
    reason: str


REPOS_TO_TEST: list[ConsumerRepo] = [
    ConsumerRepo(
        name="process_description",
        git_url="https://github.com/eclipse-score/process_description.git",
        commands=[
            "bazel run //:ide_support",
            "bazel run //:docs_check",
            "bazel run //:docs",
            "bazel build //:needs_json",
        ],
        test_commands=[],
    ),
    ConsumerRepo(
        name="score",
        git_url="https://github.com/eclipse-score/score.git",
        commands=[
            "bazel run //:ide_support",
            "bazel run //:docs_check",
            "bazel run //:docs",
            "bazel build //:needs_json",
        ],
        test_commands=[],
    ),
    ConsumerRepo(
        name="module_template",
        git_url="https://github.com/eclipse-score/module_template.git",
        commands=[
            "bazel run //:ide_support",
            "bazel run //:docs_check",
            "bazel run //:docs",
            "bazel build //:needs_json",
        ],
        test_commands=[
            "bazel test //tests/...",
        ],
    ),
]


@pytest.fixture(scope="module")
def sphinx_base_dir(tmp_path_factory: TempPathFactory, pytestconfig: Config) -> Path:
    """Create base directory for testing - either temporary or persistent cache"""
    disable_cache: bool = bool(pytestconfig.getoption("--disable-cache"))

    if disable_cache:
        # Use persistent cache directory for local development
        temp_dir = tmp_path_factory.mktemp("testing_dir")
        console.print(f"[blue]Using temporary directory: {temp_dir}[/blue]")
        return temp_dir

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]Using persistent cache directory: {CACHE_DIR}[/green]")
    return CACHE_DIR


def cleanup(cwd: Path, cmd: str):
    """
    Cleanup before tests are run
    """
    for p in cwd.glob("*/ubproject.toml"):
        p.unlink()
    shutil.rmtree(cwd / "_build", ignore_errors=True)
    if cmd == "bazel run //:ide_support":
        shutil.rmtree(cwd / ".venv_docs", ignore_errors=True)
        cmd = "bazel clean --async"
    subprocess.run(cmd.split(), text=True, cwd=cwd)


def get_current_git_commit(git_repo: Path):
    """
    Get the current git commit hash (HEAD).
    """
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
        cwd=git_repo,
    )
    return result.stdout.strip()



def comment_out_git_override(module_content: str) -> str:
    """
    Comment out existing override blocks for score_docs_as_code only.
    Handles git_override, single_version_override, local_path_override, archive_override, etc.
    """
    lines = module_content.splitlines()
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this line starts a git_override block
        if re.match(r"^\s*\w+_override\s*\(", line):
            # Collect the entire block
            block_start = i
            depth = line.count("(") - line.count(")")
            i += 1

            while i < len(lines) and depth > 0:
                depth += lines[i].count("(") - lines[i].count(")")
                i += 1

            # Extract the block
            block = lines[block_start:i]
            block_text = "\n".join(block)

            # Comment out if it's for score_docs_as_code
            if (
                'module_name = "score_docs_as_code"' in block_text
                or "module_name = 'score_docs_as_code'" in block_text
            ):
                result.extend("# " + line if line.strip() else "#" for line in block)
            else:
                result.extend(block)
        else:
            result.append(line)
            i += 1

    return "\n".join(result) + ("\n" if module_content.endswith("\n") else "")


def replace_bazel_dep_with_local_override(module_content: str) -> str:
    # Match bazel_dep with required name and optional version
    pattern = r'bazel_dep\(name = "score_docs_as_code"(?:, version = "[^"]+")?\)'

    replacement = """bazel_dep(name = "score_docs_as_code")
local_path_override(
    module_name = "score_docs_as_code",
    path = "../docs_as_code"
)"""
    return re.sub(pattern, replacement, module_content)


def replace_bazel_dep_with_git_override(
    module_content: str, git_hash: str, gh_url: str
) -> str:
    pattern = r'bazel_dep\(name = "score_docs_as_code"(?:, version = "[^"]+")?\)'

    replacement = f'''bazel_dep(name = "score_docs_as_code")
git_override(
    module_name = "score_docs_as_code",
    remote = "{gh_url}",
    commit = "{git_hash}"
)'''

    return re.sub(pattern, replacement, module_content)


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape sequences from text"""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


def parse_bazel_output(BR: BuildOutput, pytestconfig: Config) -> BuildOutput:
    err_lines = BR.stderr.splitlines()
    split_warnings = [x for x in err_lines if "WARNING: " in x]
    warning_dict: dict[str, list[str]] = defaultdict(list)

    if pytestconfig.get_verbosity() >= 2 and os.getenv("CI"):
        console.print("[DEBUG] Raw warnings in CI:")
        for i, warning in enumerate(split_warnings):
            console.print(f"[DEBUG] Warning {i}: {repr(warning)}")

    for raw_warning in split_warnings:
        # In the CLI we seem to have some ansi codes in the warnings.
        # Need to strip those
        clean_warning = strip_ansi_codes(raw_warning).strip()

        logger = "[NO SPECIFIC LOGGER]"
        file_and_warning = clean_warning

        if clean_warning.endswith("]"):
            tmp_split_warning = clean_warning.split()
            logger = tmp_split_warning[-1].upper()
            file_and_warning = clean_warning.replace(logger, "").rstrip()

        warning_dict[logger].append(file_and_warning)
    BR.warnings = warning_dict
    return BR


def print_overview_logs(BR: BuildOutput):
    warning_loggers = list(BR.warnings.keys())
    len_left_test_result = len_max - len("TEST RESULTS")
    console.print(
        f"[blue]{'=' * int(len_left_test_result / 2)}"
        f"TEST RESULTS"
        f"{'=' * int(len_left_test_result / 2)}[/blue]"
    )
    console.print(f"[navy_blue]{'=' * len_max}[/navy_blue]")
    warning_total_loggers_msg = f"Warning Loggers Total: {len(warning_loggers)}"
    len_left_loggers = len_max - len(warning_total_loggers_msg)
    console.print(
        f"[blue]{'=' * int(len_left_loggers / 2)}"
        f"{warning_total_loggers_msg}"
        f"{'=' * int(len_left_loggers / 2)}[/blue]"
    )
    warning_loggers = list(BR.warnings.keys())
    warning_total_msg = "Logger Warnings Accumulated"
    len_left_loggers_total = len_max - len(warning_total_msg)
    console.print(
        f"[blue]{'=' * int(len_left_loggers_total / 2)}"
        f"{warning_total_msg}"
        f"{'=' * int(len_left_loggers_total / 2)}[/blue]"
    )
    for logger in warning_loggers:
        if len(BR.warnings[logger]) == 0:
            continue
        color = "orange1" if logger == "[NO SPECIFIC LOGGER]" else "red"
        warning_logger_msg = f"{logger} has {len(BR.warnings[logger])} warnings"
        len_left_logger = len_max - len(warning_logger_msg)
        console.print(
            f"[{color}]{'=' * int(len_left_logger / 2)}"
            f"{warning_logger_msg}"
            f"{'=' * int(len_left_logger / 2)}[/{color}]"
        )
    console.print(f"[blue]{'=' * len_max}[/blue]")


def verbose_printout(BR: BuildOutput):
    """Prints warnings for each logger when '-v' or higher is specified."""
    warning_loggers = list(BR.warnings.keys())
    for logger in warning_loggers:
        len_left_logger = len_max - len(logger)
        console.print(
            f"[cornflower_blue]{'=' * int(len_left_logger / 2)}"
            f"{logger}"
            f"{'=' * int(len_left_logger / 2)}[/cornflower_blue]"
        )
        warnings = BR.warnings[logger]
        len_left_warnings = len_max - len(f"Warnings Found: {len(warnings)}\n")
        color = "red"
        if logger == "[NO SPECIFIC LOGGER]":
            color = "orange1"
        console.print(
            f"[{color}]{'=' * int(len_left_warnings / 2)}"
            f"{f'Warnings Found: {len(warnings)}'}"
            f"{'=' * int(len_left_warnings / 2)}[/{color}]"
        )
        console.print("\n".join(f"[{color}]{x}[/{color}]" for x in warnings))


def print_running_cmd(repo: str, cmd: str, local_or_git: str):
    """Prints a 'Title Card' for the current command"""
    len_left_cmd = len_max - len(cmd)
    len_left_repo = len_max - len(repo)
    len_left_local = len_max - len(local_or_git)
    console.print(f"\n[cyan]{'=' * len_max}[/cyan]")
    console.print(
        f"[cornflower_blue]{'=' * int(len_left_repo / 2)}"
        f"{repo}"
        f"{'=' * int(len_left_repo / 2)}[/cornflower_blue]"
    )
    console.print(
        f"[cornflower_blue]{'=' * int(len_left_local / 2)}"
        f"{local_or_git}"
        f"{'=' * int(len_left_local / 2)}[/cornflower_blue]"
    )
    console.print(
        f"[cornflower_blue]{'=' * int(len_left_cmd / 2)}"
        f"{cmd}"
        f"{'=' * int(len_left_cmd / 2)}[/cornflower_blue]"
    )
    console.print(f"[cyan]{'=' * len_max}[/cyan]")


def analyze_build_success(BR: BuildOutput) -> tuple[bool, str]:
    """
    Analyze if the build should be considered successful based on your rules.

    Rules:
    - '[NO SPECIFIC LOGGER]' warnings are always ignored
    """

    # Unsure if this is good, as sometimes the returncode is 1
    # but it should still go through?
    # Logging for feedback here
    if BR.returncode != 0:
        return False, f"Build failed with return code {BR.returncode}"

    # Check for critical/non ignored warnings
    critical_warnings = []

    for logger, warnings in BR.warnings.items():
        if logger == "[NO SPECIFIC LOGGER]":
            # Always ignore these
            continue
        # Any other logger is critical/not ignored
        critical_warnings.extend(warnings)

    if critical_warnings:
        return False, f"Found {len(critical_warnings)} critical warnings"

    return True, "Build successful - no critical warnings"


def print_final_result(BR: BuildOutput, repo_name: str, cmd: str, pytestconfig: Config):
    """
    Print your existing detailed output plus a clear success/failure summary
    """
    print_overview_logs(BR)
    if pytestconfig.get_verbosity() >= 1:
        # Verbosity Level 1 (-v)
        verbose_printout(BR)
    if pytestconfig.get_verbosity() >= 2:
        # Verbosity Level 2 (-vv)
        console.print("==== STDOUT ====:\n\n", BR.stdout)
        console.print("==== STDERR ====:\n\n", BR.stderr)

    is_success, reason = analyze_build_success(BR)

    status = "OK PASSED" if is_success else "XX FAILED"
    color = "green" if is_success else "red"

    # Printing a small 'report' for each cmd.
    result_msg = f"{repo_name} - {cmd}: {status}"
    len_left = len_max - len(result_msg)
    console.print(
        f"[{color}]{'=' * int(len_left / 2)}"
        f"{result_msg}"
        f"{'=' * int(len_left / 2)}[/{color}]"
    )
    console.print(f"[{color}]Reason: {reason}[/{color}]")
    console.print(f"[{color}]{'=' * len_max}[/{color}]")

    return is_success, reason


def print_result_table(results: list[Result]):
    """Printing an 'overview' table to show all results."""
    table = Table(title="Docs-As-Code Consumer Test Result", box=box.MARKDOWN)
    table.add_column("Repository")
    table.add_column("CMD")
    table.add_column("LOCAL OR GIT")
    table.add_column("PASSED")
    table.add_column("REASON")
    for result in results:
        style = "green" if result.passed else "red"
        table.add_row(
            result.repo,
            result.cmd,
            result.local_or_git,
            str(result.passed),
            result.reason,
            style=style,
        )
    console.print(table)


def stream_subprocess_output(cmd: str, repo_name: str, cwd: Path):
    """Stream subprocess output in real-time for maximum verbosity"""
    console.print(f"[green]Streaming output for: {cmd}[/green]")

    process = subprocess.Popen(
        cmd.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Merge stderr into stdout
        universal_newlines=True,
        bufsize=1,
        cwd=cwd,
    )

    # Stream output line by line
    output_lines = []
    if process.stdout is not None:
        for line in iter(process.stdout.readline, ""):
            if line:
                console.print(line.rstrip())  # Print immediately
                output_lines.append(line)

        process.stdout.close()
    return_code = process.wait()

    return BuildOutput(
        returncode=return_code,
        stdout="".join(output_lines),
        stderr="",  # All merged into stdout
    )


def run_cmd(
    cmd: str,
    results: list[Result],
    repo_name: str,
    local_or_git: str,
    pytestconfig: Config,
    cwd: Path,
) -> tuple[list[Result], bool]:
    verbosity: int = pytestconfig.get_verbosity()

    cleanup(cwd, cmd)

    if verbosity >= 3:
        # Level 3 (-vvv): Stream output in real-time
        BR = stream_subprocess_output(cmd, repo_name, cwd)
    else:
        # Level 0-2: Capture output and parse later
        out = subprocess.run(cmd.split(), capture_output=True, text=True, cwd=cwd)
        BR = BuildOutput(
            returncode=out.returncode,
            stdout=str(out.stdout),
            stderr=str(out.stderr),
        )

    # Parse warnings (only needed for non-streaming mode)
    if verbosity < 3:
        BR = parse_bazel_output(BR, pytestconfig)
    else:
        # For streaming mode, we can't parse warnings from stderr easily
        # since everything was merged to stdout and already printed
        BR.warnings = {}

    is_success, reason = print_final_result(BR, repo_name, cmd, pytestconfig)

    results.append(
        Result(
            repo=repo_name,
            cmd=cmd,
            local_or_git=local_or_git,
            passed=is_success,
            reason=reason,
        )
    )

    return results, is_success


def setup_test_environment(sphinx_base_dir: Path, pytestconfig: Config):
    """Set up the test environment and return necessary paths and metadata."""
    git_root = find_git_root()

    assert git_root, "Git root was not found"

    gh_url = get_github_base_url(git_root)
    current_hash = get_current_git_commit(git_root)

    verbosity: int = pytestconfig.get_verbosity()

    def debug_print(message: str):
        if verbosity >= 2:
            print(f"[DEBUG] {message}")

    debug_print(f"git_root: {git_root}")

    # Get GitHub URL and current hash for git override
    debug_print(f"gh_url: {gh_url}")
    debug_print(f"current_hash: {current_hash}")
    debug_print(
        "Working directory has uncommitted changes: "
        f"{has_uncommitted_changes(git_root)}"
    )

    def recreate_symlink(dest: Path, target: Path):
        # Create symlink for local docs-as-code
        if dest.exists() or dest.is_symlink():
            # Remove existing symlink/directory to recreate it
            if dest.is_symlink():
                dest.unlink()
                debug_print(f"Removed existing symlink: {dest}")
            elif dest.is_dir():
                import shutil

                shutil.rmtree(dest)
                debug_print(f"Removed existing directory: {dest}")
        dest.symlink_to(target)
        debug_print(f"Symlink created: {dest} -> {target}")

    recreate_symlink(sphinx_base_dir / "docs_as_code", git_root)

    return gh_url, current_hash


def has_uncommitted_changes(path: Path) -> bool:
    """Check if there are uncommitted changes in the git repo."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=path,
    )
    return bool(result.stdout.strip())


def clone_or_update_repo(repo_path: Path, git_url: str, use_cache: bool = True):
    """Clone the repository if it doesn't exist, or update it if it does."""
    if repo_path.exists():
        if use_cache:
            console.print(f"[green]Using cached repository: {repo_path.name}[/green]")
            # Update the existing repo
            subprocess.run(
                ["git", "fetch", "origin"],
                check=True,
                capture_output=True,
                cwd=repo_path,
            )
            subprocess.run(
                ["git", "reset", "--hard", "origin/main"],
                check=True,
                capture_output=True,
                cwd=repo_path,
            )
        else:
            console.print(f"[yellow]Re-cloning repository: {repo_path.name}[/yellow]")
            import shutil

            shutil.rmtree(repo_path)
            subprocess.run(
                ["git", "clone", git_url],
                check=True,
                capture_output=True,
                cwd=repo_path.parent,
            )
    else:
        console.print(f"[green]Cloning repository: {repo_path.name}[/green]")
        subprocess.run(
            ["git", "clone", git_url],
            check=True,
            capture_output=True,
            cwd=repo_path.parent,
        )


def get_repo_overrides(repo_path: Path, current_hash: str, gh_url: str):
    """Prepare both local and git overrides."""

    # Read original MODULE.bazel
    module_orig = (repo_path / "MODULE.bazel").read_text(encoding="utf-8")

    # Prepare override versions
    module_orig_clean = comment_out_git_override(module_orig)
    module_local_override = replace_bazel_dep_with_local_override(module_orig_clean)
    module_git_override = replace_bazel_dep_with_git_override(
        module_orig_clean, current_hash, gh_url
    )

    return module_local_override, module_git_override


@pytest.fixture(scope="module")
def consumer_env(sphinx_base_dir: Path, pytestconfig: Config) -> tuple[str, str]:
    return setup_test_environment(sphinx_base_dir, pytestconfig)


@pytest.mark.parametrize(
    "consumer_params",
    [(repo, override) for repo in REPOS_TO_TEST for override in ("local", "git")],
    ids=[
        f"{repo.name}-{override}"
        for repo in REPOS_TO_TEST
        for override in ("local", "git")
    ],
)
def test_consumer_repo(
    consumer_params: tuple[ConsumerRepo, str],
    sphinx_base_dir: Path,
    consumer_env: tuple[str, str],
    pytestconfig: Config,
):
    repo, override_type = consumer_params
    gh_url, current_hash = consumer_env
    disable_cache: bool = bool(pytestconfig.getoption("--disable-cache"))

    len_left_repo = len_max - len(repo.name)
    console.print(f"{'=' * len_max}")
    console.print(
        f"{'=' * int(len_left_repo / 2)}{repo.name}{'=' * int(len_left_repo / 2)}"
    )

    repo_path = sphinx_base_dir / repo.name
    clone_or_update_repo(repo_path, repo.git_url, use_cache=not disable_cache)

    module_local_override, module_git_override = get_repo_overrides(
        repo_path, current_hash, gh_url
    )
    override_content = (
        module_local_override if override_type == "local" else module_git_override
    )
    (repo_path / "MODULE.bazel").write_text(override_content, encoding="utf-8")

    results: list[Result] = []
    overall_success = True

    for cmd in repo.commands:
        print_running_cmd(repo.name, cmd, f"{override_type.upper()} OVERRIDE")
        results, is_success = run_cmd(
            cmd, results, repo.name, override_type, pytestconfig, cwd=repo_path
        )
        if not is_success:
            overall_success = False

    for test_cmd in repo.test_commands:
        print_running_cmd(repo.name, test_cmd, f"{override_type.upper()} OVERRIDE")
        results, is_success = run_cmd(
            test_cmd, results, repo.name, override_type, pytestconfig, cwd=repo_path
        )
        if not is_success:
            overall_success = False

    print_result_table(results)
    if not overall_success:
        pytest.fail(
            reason="Consumer Tests failed, see table for which commands specifically."
        )
