#!/usr/bin/env python3


import sys
import venv
import subprocess
import glob
import os
import re


MINIMUM_TEST_COVERAGE = 100
COVERAGE_FLAGS = "--show-missing --skip-covered --skip-empty --omit=financial_game/__main__.py"
RUN_PORT = 8000
RUN_DEBUG = "--debug"
RUN_DATABASE = os.path.abspath("objects/test.sqlite3")
RUN_RESET_SCRIPT = "initial_db.yaml"
PYTHON_SOURCE_DIR = 'financial_game'
RUN_ARGS = f"--port {RUN_PORT} --db {RUN_DATABASE} {RUN_DEBUG} --reset {RUN_RESET_SCRIPT}"
PYTHON_SOURCES = os.path.join(PYTHON_SOURCE_DIR, '*.py')
REQUIREMENTS_PATH = 'requirements.txt'
VENV_PATH = '.venv'
FLAKE8_FLAGS='--max-line-length=100'
GITHUB_WORKFLOW = os.environ.get('GITHUB_WORKFLOW', '') == 'CI'
ERROR_PREFIX = "##[error]" if GITHUB_WORKFLOW else "💥💥"
LINT_ERROR_PATTERN = re.compile(r'^(.*:.*:.*:)', re.MULTILINE)
PIP_QUIET = '' if GITHUB_WORKFLOW else '--quiet'


def run_in_env(command:str, venv:str=VENV_PATH, dump:bool=True, check:bool=True) -> str:
    results = subprocess.run(('bash', '-c', f"source .venv/bin/activate && {command}"), check=check, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout = results.stdout.decode('utf-8')
    stderr = results.stderr.decode('utf-8')

    if dump:
        sys.stdout.write(stdout)
        sys.stderr.write(stderr)

    return (results.returncode, stdout, stderr)


def github_log(text:str):
    if GITHUB_WORKFLOW:
        print(text)

if __name__ == "__main__":

    #####################################
    #
    #  Python venv
    #
    #####################################
    github_log("##[group] Installing dependencies")
    github_log(f"##[command]python3 -m venv {VENV_PATH}")
    venv.create(VENV_PATH, symlinks=True, with_pip=True)
    github_log(f"##[command]pip3 install {PIP_QUIET} --upgrade pip")
    run_in_env(f"pip install {PIP_QUIET} --upgrade pip")
    github_log(f"##[command]pip3 install {PIP_QUIET} --requirement {REQUIREMENTS_PATH}")
    run_in_env(f"pip install {PIP_QUIET} --requirement {REQUIREMENTS_PATH}")
    github_log("##[endgroup]")

    #####################################
    #
    #  Start parallel processes
    #
    #####################################
    black_check = '--check' if len(sys.argv) == 1 else ''
    sources = " ".join(glob.glob(PYTHON_SOURCES))

    #####################################
    #
    #  black Python formatting / linting
    #
    #####################################
    github_log("##[group] Running black python source validation")
    github_log(f"##[command]python3 -m black {black_check} {sources}")
    (return_code, stdout, stderr) = run_in_env(f"python3 -m black {black_check} {sources}", check=False)
    return_codes = [return_code]
    github_log("##[endgroup]")

    if return_code != 0:
        print(f"{ERROR_PREFIX}💥💥 Please run black on this source to reformat and resubmit 💥💥 ")
    else:
        print("✅ black verification successful")

    #####################################
    #
    #  pylint Python linting
    #
    #####################################
    github_log("##[group] Running pylint python source validation")
    github_log(f"##[command]pylint {sources}")
    (return_code, stdout, stderr) = run_in_env(f"pylint {sources}", check=False, dump=False)
    return_codes.append(return_code)
    stdout = LINT_ERROR_PATTERN.sub(f"{ERROR_PREFIX}\\1", stdout)
    stderr = LINT_ERROR_PATTERN.sub(f"{ERROR_PREFIX}\\1", stderr)
    sys.stdout.write(stdout)
    sys.stderr.write(stderr)
    github_log("##[endgroup]")

    if return_code != 0:
        print(f"{ERROR_PREFIX}💥💥 Please fix the above pylint errors and resubmit 💥💥 ")
    else:
        print("✅ pylint verification successful")

    #####################################
    #
    #  flake8 Python linting
    #
    #####################################
    github_log("##[group] Running flake8 python source validation")
    github_log("##[command]flake8 {FLAKE8_FLAGS} {sources}")
    (return_code, stdout, stderr) = run_in_env(f"flake8 {FLAKE8_FLAGS} {sources}", check=False, dump=False)
    return_codes.append(return_code)
    stdout = LINT_ERROR_PATTERN.sub(f"{ERROR_PREFIX}\\1", stdout)
    stderr = LINT_ERROR_PATTERN.sub(f"{ERROR_PREFIX}\\1", stderr)
    sys.stdout.write(stdout)
    sys.stderr.write(stderr)
    github_log("##[endgroup]")

    if return_code != 0:
        print(f"{ERROR_PREFIX}💥💥 Please fix the above flake8 errors and resubmit 💥💥 ")
    else:
        print("✅ flake8 verification successful")

    #####################################
    #
    #  Run Python unit tests
    #
    #####################################
    github_log("##[group] Running python unit tests")
    github_log(f"##[command]python3 -m coverage run --source={PYTHON_SOURCE_DIR} -m pytest")
    (return_code, stdout, stderr) = run_in_env(f"python3 -m coverage run --source={PYTHON_SOURCE_DIR} -m pytest", check=False)
    return_codes.append(return_code)
    github_log("##[endgroup]")

    if return_code != 0:
        print(f"{ERROR_PREFIX}💥💥 Please fix the above test failures and resubmit 💥💥 ")
    else:
        print("✅ unit tests passed")

    #####################################
    #
    #  Evaluate Python unit test coverage
    #
    #####################################

    github_log("##[group] Checking python unit test coverage")
    github_log(f"##[command]python3 -m coverage report --fail-under={MINIMUM_TEST_COVERAGE} {COVERAGE_FLAGS}")
    (return_code, stdout, stderr) = run_in_env(f"python3 -m coverage report --fail-under={MINIMUM_TEST_COVERAGE} {COVERAGE_FLAGS}", check=False)
    return_codes.append(return_code)
    github_log("##[endgroup]")

    if return_code != 0:
        print(f"{ERROR_PREFIX}💥💥 Please bring test coverage to $MINIMUM_TEST_COVERAGE% and resubmit 💥💥 ")
    else:
        print("✅ sufficient test coverage")

    #####################################
    #
    #  Run Python app in testing mode
    #
    #####################################
    if "run" in sys.argv:
        run_in_env(f"python3 -m {PYTHON_SOURCE_DIR} {RUN_ARGS}", check=False)


    #####################################
    #
    #  Return failing status
    #
    #####################################
    if any(r != 0 for r in return_codes):
        sys.exit(sum(return_codes) if sum(return_codes) != 0 else 1)
