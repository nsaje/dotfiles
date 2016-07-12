function red {
  echo -e "\e[31m$1\e[0m"
}

function blue {
  echo -e "\e[34m$1\e[0m"
}

blue "PEP8 lint in progress ..."
pep8 \
  --first \
  --exclude="test_api.py,settings.py,wsgi.py,migrations,actionlog,localsettings.py,regions.py" \
  --max-line-length=700 \
  ./server/

if [ $? != 0 ]
  then
    red "+-------------------------+"
    red "|    PEP8 CHECK FAILED    |"
    red "+-------------------------+"
    exit 1
fi
blue "PEP8 check successful"

blue "ESLint in progress ..."
eslint client/one/js

if [ $? != 0 ]
  then
    red "+---------------------------+"
    red "|    ESLINT CHECK FAILED    |"
    red "+---------------------------+"
    exit 1
fi
blue "ESLint check successful"
