#!/bin/bash
if [ ! -f /.initialized ]; then

    echo "getting ready"
    apt-get update
    apt-get install -y libgsl-dev
    pip install --no-cache-dir cython cysignals
    pip install --no-cache-dir git+https://github.com/umbibio/nlbayes-python.git
    pip install --no-cache-dir celery[librabbitmq,redis] pymongo

    ln -s /opt/app/nlbayes_tasks.py /opt/
    touch /.initialized
fi

exec "$@"
