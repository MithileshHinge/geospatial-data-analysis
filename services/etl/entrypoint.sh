#!/bin/bash

cd /tmp/lib/tsg_common/db
alembic upgrade head
cd /app
/opt/conda/bin/python main.py