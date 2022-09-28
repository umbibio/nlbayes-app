#!/bin/bash

if [ ! -f /.initialized ]; then

    echo "getting ready"
    pip install --upgrade pip
    pip install --no-cache-dir celery[librabbitmq,redis] pymongo numpy pandas openpyxl xlrd
    pip install --no-cache-dir dash dash-bootstrap-components dash-bootstrap-templates dash-cytoscape gunicorn

    touch /.initialized
fi

exec "$@"
