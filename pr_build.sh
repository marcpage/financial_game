#!bash


#####################################
#
#  Settings
#
#####################################

export MINIMUM_TEST_COVERAGE=100
export SOURCE_DIR=financial_game
export SOURCES="$SOURCE_DIR/*.py"
export VENV_DIR=.venv
export REQUIREMENTS_PATH=requirements.txt
export FLAKE8_FLAGS=--max-line-length=100
export COVERAGE_FLAGS="--show-missing --skip-covered --skip-empty --omit=financial_game/__main__.py"
export OBJECTS_DIR=objects
export PYLINT_OUTPUT=$OBJECTS_DIR/pylint_output.txt
export FLAKE8_OUTPUT=$OBJECTS_DIR/flake8_output.txt

mkdir -p $OBJECTS_DIR
rm -f $PYLINT_OUTPUT
rm -f $FLAKE8_OUTPUT

#####################################
#
#  CI behavior
#
#####################################

if [ "$GITHUB_WORKFLOW" = "CI" ]; then
    export LOG_ECHO=echo
    export ERROR_PREFIX="##[error]"
    export WARNING_PREFIX="##[warning]"
else
    export ERROR_PREFIX="💥💥"
    export LOG_ECHO=true
fi


#####################################
#
#  Python venv
#
#####################################

$LOG_ECHO "##[group] Installing dependencies"
mkdir -p $VENV_DIR
$LOG_ECHO "##[command]python3 -m venv $VENV_DIR"
python3 -m venv $VENV_DIR
$LOG_ECHO "##[command]. $VENV_DIR/bin/activate"
. $VENV_DIR/bin/activate
$LOG_ECHO "##[command]pip3 install --quiet --upgrade pip"
pip3 install --quiet --upgrade pip
$LOG_ECHO "##[command]pip3 install --quiet --requirement $REQUIREMENTS_PATH"
pip3 install --quiet --requirement $REQUIREMENTS_PATH
$LOG_ECHO "##[endgroup]"


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
pylint --output $PYLINT_OUTPUT $SOURCES
export PYLINT_STATUS=$?
cat $PYLINT_OUTPUT | sed 's/^\(.*:.*:.*:\)/'$ERROR_PREFIX'\1/'
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
flake8  --output-file $FLAKE8_OUTPUT $FLAKE8_FLAGS $SOURCES
export FLAKE8_STATUS=$?
cat $FLAKE8_OUTPUT | sed 's/^\(.*:.*:.*:\)/'$ERROR_PREFIX'\1/'
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
$LOG_ECHO "##[command]python3 -m coverage run --source=$SOURCE_DIR -m pytest"
python3 -m coverage run --source=$SOURCE_DIR -m pytest
export TEST_STATUS=$?
$LOG_ECHO "##[command]python3 -m coverage report --fail-under=$MINIMUM_TEST_COVERAGE $COVERAGE_FLAGS"
python3 -m coverage report --fail-under=$MINIMUM_TEST_COVERAGE $COVERAGE_FLAGS
export COVERAGE_STATUS=$?
$LOG_ECHO "##[endgroup]"
if [ $TEST_STATUS -ne 0 ]; then
    echo $ERROR_PREFIX"💥💥 Please fix the above test failures and resubmit 💥💥 "
else
    echo "✅ unit tests passed"
fi
if [ $COVERAGE_STATUS -ne 0 ]; then
    echo $ERROR_PREFIX"💥💥 Please bring test coverage to $MINIMUM_TEST_COVERAGE% and resubmit 💥💥 "
else
    echo "✅ sufficient test coverage"
fi


#####################################
#
#  Run Python app in testing mode
#
#####################################

if [ "$1" = "run" ]; then python3 -m $SOURCE_DIR --test; fi


#####################################
#
#  Return failing status
#
#####################################

exit $(($BLACK_STATUS + $PYLINT_STATUS + $FLAKE8_STATUS + $TEST_STATUS + $COVERAGE_STATUS))
