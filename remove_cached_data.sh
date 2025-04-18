#!/bin/bash

# Create and run a Docker container with a bind mount to the current directory
docker run -it \
  -v "${PWD}/:/data" \
  ubuntu bash -c "
    # Navigate to the data directory
    cd /data && \
    
    # Remove the specified directories
    rm -r backend/redis/redis-data && \
    rm -r postgres_data && \
    rm -r backend/res-immunology-automation/res_immunology_automation/src/scripts/cached_data_json && \
    rm -r backend/res-immunology-automation/res_immunology_automation/src/scripts/logs && \
    
    # Exit the container
    exit
  "

# Notify the user
echo "Cached data removed successfully."
