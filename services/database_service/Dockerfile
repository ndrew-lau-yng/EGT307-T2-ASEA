# Use the official PostgreSQL 16 image
FROM postgres:16-alpine

# Copy init.sql into Postgres init directory
# Runs automatically on container startup
# "01-" prefix ensures execution order 
COPY init.sql /docker-entrypoint-initdb.d/01-init.sql