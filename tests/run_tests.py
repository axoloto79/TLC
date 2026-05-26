import subprocess
import sys
import re
import tempfile
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"
TESTS = ROOT / "tests"
ANASYN = SRC / "anasyn.py"

GREEN = "\033[32m"
RED   = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

VM_RUNNER = f"""
import sys
sys.path.insert(0, r'{SRC}')
from vm import VirtualMachine
vm = VirtualMachine()
vm.load_code_from_file(sys.argv[1])
vm.run()
"""

def get_expected_errors(path: Path) -> list[str]:
    lines = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\s*//!\s*(.*)", line)
        if m:
            lines.append(m.group(1).strip())
    return lines

def get_expected_output(path: Path) -> list[str]:
    lines = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\s*//>\s*(.*)", line)
        if m:
            lines.append(m.group(1).strip())
    return lines

def count_get_calls(path: Path) -> int:
    return len(re.findall(r"\bget\(", path.read_text(encoding="utf-8", errors="replace")))

def compile_file(src_path: Path, out_path: Path) -> tuple[bool, str]:
    r = subprocess.run(
        [sys.executable, str(ANASYN), str(src_path), "-o", str(out_path)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    return r.returncode == 0, r.stderr

def run_vm(co_path: Path, stdin: str = "") -> tuple[str, str]:
    r = subprocess.run(
        [sys.executable, "-c", VM_RUNNER, str(co_path)],
        capture_output=True, text=True, input=stdin, timeout=10, cwd=str(ROOT),
    )
    return r.stdout, r.stderr

def extract_put_outputs(raw: str) -> list[str]:
    """Keep only lines that look like put() output (numbers / booleans)."""
    result = []
    for line in raw.splitlines():
        line = line.strip()
        if re.match(r"^-?\d+$|^True$|^False$", line):
            result.append(line)
    return result

def run_test(path: Path) -> tuple[bool, str]:
    is_error = path.stem.startswith("error")
    expected = get_expected_output(path)
    num_gets = count_get_calls(path)
    stdin = "0\n" * num_gets

    with tempfile.NamedTemporaryFile(suffix=".co", delete=False) as f:
        co = Path(f.name)

    try:
        ok, err_msg = compile_file(path, co)

        if is_error:
            if not ok:
                expected_msgs = get_expected_errors(path)
                for msg in expected_msgs:
                    if msg not in err_msg:
                        return False, (
                            f"compile failed but wrong error message\n"
                            f"  expected substring: {msg!r}\n"
                            f"  actual stderr:      {err_msg.strip()}"
                        )
                return True, "compile error as expected"
            return False, "expected compile error but succeeded"

        if not ok:
            return False, f"unexpected compile error:\n{err_msg.strip()}"

        try:
            stdout, stderr = run_vm(co, stdin)
        except subprocess.TimeoutExpired:
            return False, "VM timeout"

        if stderr.strip():
            return False, f"VM error:\n{stderr.strip()}"

        if not expected:
            return True, "compiled and ran OK"

        actual = extract_put_outputs(stdout)
        if actual[: len(expected)] == expected:
            return True, f"output OK: {actual}"
        return False, f"wrong output\n  expected: {expected}\n  got:      {actual}"

    finally:
        co.unlink(missing_ok=True)


def main():
    test_dirs = [
        ("nna",        sorted((TESTS / "nna").glob("*.nno"))),
        ("nnp",        sorted((TESTS / "nnp").glob("*.nno"))),
        ("test_perso", sorted((TESTS / "test_perso").glob("*.nnp"))),
    ]

    total = passed = 0

    for group, files in test_dirs:
        print(f"\n{'─'*50}")
        print(f"  {group}")
        print(f"{'─'*50}")
        for path in files:
            total += 1
            ok, msg = run_test(path)
            passed += ok
            status = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
            print(f"  {status}  {path.name}")
            if not ok:
                for line in msg.splitlines():
                    print(f"        {line}")

    print(f"\n{'─'*50}")
    color = GREEN if passed == total else RED
    print(f"  {color}{passed}/{total} tests passed{RESET}")
    print(f"{'─'*50}\n")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
