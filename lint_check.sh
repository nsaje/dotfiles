function red {
  echo -e "\e[31m$1\e[0m"
}

function blue {
  echo -e "\e[34m$1\e[0m"
}

function green {
  echo -e "\e[32m$1\e[0m"
}

# PEP 8 ------------------------------------------------------------------------

blue "PEP8 lint in progress ..."
pep8 \
  --first \
  --exclude="__init__.py,test_api.py,settings.py,wsgi.py,migrations,actionlog,localsettings.py,regions.py" \
  --max-line-length=700 \
  ./server/

if [ $? != 0 ]
  then
    red "+-------------------------+"
    red "|    PEP8 CHECK FAILED    |"
    red "+-------------------------+"
    exit 1
fi
green "PEP8 check successful"

# ES Lint ----------------------------------------------------------------------

blue "ESLint in progress ..."
eslint client/one client/test

if [ $? != 0 ]
  then
    red "+---------------------------+"
    red "|    ESLINT CHECK FAILED    |"
    red "+---------------------------+"
    exit 1
fi
green "ESLint check successful"

# Xenon ------------------------------------------------------------------------

blue "Xenon (cyclomatic complexity) check in progress ..."
xenon \
  --max-absolute D \
  -e "server/dash/table.py,server/dash/views/views.py,server/dash/dashapi/api_breakdowns.py" \
  ./server/

if [ $? != 0 ]
  then
    red "+---------------------------+"
    red "|    XENON CHECK FAILED     |"
    red "+---------------------------+"
    exit 1
fi
green "Xenon check successful"
