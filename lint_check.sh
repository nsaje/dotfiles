function red {
  echo -e "\e[31m$1\e[0m"
}

function blue {
  echo -e "\e[34m$1\e[0m"
}

function green {
  echo -e "\e[32m$1\e[0m"
}

# Flake8 ------------------------------------------------------------------------

blue "Flake8 lint in progress ..."
flake8 ./server/

if [ $? != 0 ]
  then
    red "+-------------------------+"
    red "|    Flake8 CHECK FAILED    |"
    red "+-------------------------+"
    exit 1
fi
green "Flake8 check successful"

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
  -e "server/dash/table.py,server/dash/models.py,server/dash/views/views.py,server/dash/dashapi/api_breakdowns.py,server/core/entity/settings/ad_group_settings.py,server/core/entity/settings/ad_group_settings/model.py" \
  ./server/

if [ $? != 0 ]
  then
    red "+---------------------------+"
    red "|    XENON CHECK FAILED     |"
    red "+---------------------------+"
    exit 1
fi
green "Xenon check successful"
