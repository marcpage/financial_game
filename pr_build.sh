#!bash


#####################################
#
#  Settings
#
#####################################

export SOURCE_DIR=financial_game
export SOURCES="$SOURCE_DIR/*.py"
export APP_MAIN_SCRIPT=$SOURCE_DIR/__main__.py
export VENV_DIR=.venv
export REQUIREMENTS_PATH=requirements.txt
export FLAKE8_FLAGS=--max-line-length=100


#####################################
#
#  CI behavior
#
#####################################

if [ "$GITHUB_WORKFLOW" = "CI" ]; then
    export LOG_ECHO=echo
    export ERROR_PREFIX="##[error]"
else
    export LOG_ECHO=true
fi


#####################################
#
#  Python venv
#
#####################################

mkdir -p $VENV_DIR
python3 -m venv $VENV_DIR
. $VENV_DIR/bin/activate
pip3 install --upgrade pip
pip3 install -qr $REQUIREMENTS_PATH


#####################################
#
#  black Python formatting / linting
#
#####################################

if [ "$1" = "" ]; then export BLACK_CHECK=--check; fi
$LOG_ECHO "##[group] Running black python source validation"
$LOG_ECHO "##[command]python3 -m black $BLACK_CHECK $SOURCES"
python3 -m black $BLACK_CHECK $SOURCES
export BLACK_STATUS=$?
$LOG_ECHO "##[endgroup]"
if [ $BLACK_STATUS -ne 0 ]; then
    echo $ERROR_PREFIX"💥💥 Please run black on this source to reformat and resubmit 💥💥 "
else
    echo "✅ black verification successful"
fi


#####################################
#
#  pylint Python linting
#
#####################################

$LOG_ECHO "##[group] Running pylint python source validation"
$LOG_ECHO "##[command]pylint $SOURCES"
pylint $SOURCES
export PYLINT_STATUS=$?
$LOG_ECHO "##[endgroup]"
if [ $PYLINT_STATUS -ne 0 ]; then
    echo $ERROR_PREFIX"💥💥 Please fix the above pylint errors and resubmit 💥💥 "
else
    echo "✅ pylint verification successful"
fi


#####################################
#
#  flake8 Python linting
#
#####################################

$LOG_ECHO "##[group] Running flake8 python source validation"
$LOG_ECHO "##[command]flake8 $FLAKE8_FLAGS $SOURCES"
flake8 $FLAKE8_FLAGS $SOURCES
export FLAKE8_STATUS=$?
$LOG_ECHO "##[endgroup]"
if [ $FLAKE8_STATUS -ne 0 ]; then
    echo $ERROR_PREFIX"💥💥 Please fix the above flake8 errors and resubmit 💥💥 "
else
    echo "✅ flake8 verification successful"
fi


#####################################
#
#  Run Python unit tests
#
#####################################

$LOG_ECHO "##[group] Running python unit tests"
$LOG_ECHO "##[command]python3 -m coverage run -m pytest"
python3 -m coverage run -m pytest
export TEST_STATUS=$?
python3 -m coverage report
$LOG_ECHO "##[endgroup]"
if [ $TEST_STATUS -ne 0 ]; then
    echo $ERROR_PREFIX"💥💥 Please fix the above test failures and resubmit 💥💥 "
else
    echo "✅ unit tests passed"
fi


#####################################
#
#  Run Python app in testing mode
#
#####################################

if [ "$1" = "run" ]; then python3 $APP_MAIN_SCRIPT --test; fi


#####################################
#
#  Return failing status
#
#####################################

exit $(($BLACK_STATUS + $PYLINT_STATUS + $FLAKE8_STATUS + $TEST_STATUS))
