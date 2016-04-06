#!/usr/bin/env bash
cd $( dirname $0 )
if [[ ! -d venv ]];then
    rm -f venv
    mkdir venv
    virtualenv venv
fi
. venv/bin/activate
pip install -r ./requirements.txt
pip install -r ./requirements_gunicorn.txt
cd ..
gunicorn --timeout 120 --workers 4 --pid ./frontendservice.pid --log-level=DEBUG -b 0.0.0.0:5480 frontendservice:app
