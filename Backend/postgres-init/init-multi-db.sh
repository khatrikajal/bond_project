#!/bin/bash
set -e

echo "Initializing multiple databases..."

# create bond_main_temp_test
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
SELECT 'CREATE DATABASE bond_main_temp_test'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'bond_main_temp_test'
)\gexec
EOSQL

# create bond_market_temp_test
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
SELECT 'CREATE DATABASE bond_market_temp_test'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'bond_market_temp_test'
)\gexec
EOSQL
