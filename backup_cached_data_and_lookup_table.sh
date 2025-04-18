#!/bin/bash

# Define the backup directory on the host machine
BACKUP_DIR="${PWD}/backup"

# Create the backup directory on the host machine if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Get the current user's UID and GID on the host machine
USER_ID=$(id -u)
GROUP_ID=$(id -g)

# Notify the user about the backup process
echo "Creating a copy of the specified directories in the backup folder with correct permissions..."

# Create and run a Docker container with a bind mount to the current directory
docker run -it \
  -v "${PWD}/:/data" \
  ubuntu bash -c "
    # Navigate to the data directory
    cd /data && \
    
    # Copy the specified directories to the backup folder with ownership matching the host user
    cp -r --preserve=mode backend/redis/redis-data /data/backup/ && \
    cp -r --preserve=mode postgres_data /data/backup/ && \
    cp -r --preserve=mode backend/res-immunology-automation/res_immunology_automation/src/scripts/cached_data_json /data/backup/ && \

    # Change ownership of copied files and directories to match the host user
    chown -R ${USER_ID}:${GROUP_ID} /data/backup/redis-data && \
    chown -R ${USER_ID}:${GROUP_ID} /data/backup/postgres_data && \
    chown -R ${USER_ID}:${GROUP_ID} /data/backup/cached_data_json && \

    # Exit the container
    exit
  "

# Notify the user about completion
echo "Backup of specified directories created in the host machine at '${BACKUP_DIR}' with correct permissions."
