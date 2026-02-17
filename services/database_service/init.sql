apiVersion: v1
kind: ConfigMap
metadata:
  name: db-init-sql
data:
  init.sql: |
    CREATE TABLE IF NOT EXISTS predictions (
      id SERIAL PRIMARY KEY,
      created_at TIMESTAMP DEFAULT NOW(),
      input_json JSONB NOT NULL,
      prediction_json JSONB NOT NULL
    );

    CREATE TABLE IF NOT EXISTS request_log (
      id SERIAL PRIMARY KEY,
      created_at TIMESTAMP DEFAULT NOW(),
      route TEXT NOT NULL,
      status_code INT NOT NULL,
      latency_ms INT NOT NULL
    );