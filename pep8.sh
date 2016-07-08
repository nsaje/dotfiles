function red {
  echo -e "\e[31m$1\e[0m"
}

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
