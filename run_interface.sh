#!/bin/bash

docker build -t agent-template .
docker run -it --rm \
  -p 8000:8000 \
  -v $(pwd):/workspace \
  --env-file .env \
  agent-template