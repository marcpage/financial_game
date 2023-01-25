#!/usr/bin/env python3


import sys
import venv
import subprocess
import glob
import os
import re
import threading
import queue
import shutil


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


class Start(threading.Thread):
    def __init__(self, command:str, venv:str=VENV_PATH, line_filter=None, check:bool=False):
        self.command = command
        self.venv = venv
        self.__check = check
        self.__messages = queue.Queue()
        self.__line_filter = (lambda x:x) if line_filter is None else line_filter
        self.return_code = None
        self.__process = None
        threading.Thread.__init__(self, daemon=True)
        self.start()

    def __stream(self, stream, name:str):
        for line in iter(stream.readline, ''):
            self.__messages.put((name, self.__line_filter(line)))

    def dump(self):
        streams = {'out': sys.stdout, 'err': sys.stderr}

        while self.__process is None or self.__messages.qsize() > 0 or self.__process.poll() is None:
            try:
                message = self.__messages.get(timeout=0.100)
                streams[message[0]].write(message[1])

            except queue.Empty:
                pass

        sys.stdout.flush()
        sys.stderr.flush()
        assert not self.__check or self.return_code == 0, f"Return code = {self.return_code}"
        return self.return_code

    def run(self):
        shell = shutil.which('bash')
        self.__process = subprocess.Popen((shell, '-c', f"source .venv/bin/activate && {self.command}"),stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True)
        stdout = threading.Thread(target=self.__stream, args=(self.__process.stdout, 'out'))
        stderr = threading.Thread(target=self.__stream, args=(self.__process.stderr, 'err'))
        stdout.start()
        stderr.start()
        self.return_code = self.__process.wait()
        assert not self.__check or self.return_code == 0, f"Return code = {self.return_code}"


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
    Start(f"pip install {PIP_QUIET} --upgrade pip").dump()
    github_log(f"##[command]pip3 install {PIP_QUIET} --requirement {REQUIREMENTS_PATH}")
    Start(f"pip install {PIP_QUIET} --requirement {REQUIREMENTS_PATH}").dump()
    github_log("##[endgroup]")

    #####################################
    #
    #  Start parallel processes
    #
    #####################################
    black_check = '--check' if len(sys.argv) == 1 else ''
    sources = " ".join(glob.glob(PYTHON_SOURCES))
    black = Start(f"python3 -m black {black_check} {sources}", check=False)

    if black_check:  # if black is modifying code wait until it is done
        black.join()

    pylint = Start(f"pylint {sources}", check=False, line_filter=lambda l:LINT_ERROR_PATTERN.sub(f"{ERROR_PREFIX}\\1", l))
    flake8 = Start(f"flake8 {FLAKE8_FLAGS} {sources}", check=False, line_filter=lambda l:LINT_ERROR_PATTERN.sub(f"{ERROR_PREFIX}\\1", l))
    tests = Start(f"python3 -m coverage run --source={PYTHON_SOURCE_DIR} -m pytest", check=False)

    #####################################
    #
    #  black Python formatting / linting
    #
    #####################################
    github_log("##[group] Running black python source validation")
    github_log(f"##[command]python3 -m black {black_check} {sources}")
    return_code = black.dump()
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
    return_code = pylint.dump()
    return_codes.append(return_code)
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
    return_code = flake8.dump()
    return_codes.append(return_code)
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
    return_code = tests.dump()
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
    return_code = Start(f"python3 -m coverage report --fail-under={MINIMUM_TEST_COVERAGE} {COVERAGE_FLAGS}", check=False).dump()
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
        Start(f"python3 -m {PYTHON_SOURCE_DIR} {RUN_ARGS}", check=False).dump()


    #####################################
    #
    #  Return failing status
    #
    #####################################
    if any(r != 0 for r in return_codes):
        sys.exit(sum(return_codes) if sum(return_codes) != 0 else 1)
