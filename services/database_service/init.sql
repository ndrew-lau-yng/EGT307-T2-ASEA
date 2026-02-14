-- Records inputs and outputs from model
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    input_json JSONB NOT NULL,            -- Stores input data as JSON
    prediction_json JSONB NOT NULL        -- Stores prediction result as JSON
);

--Records metadata about API requests
CREATE TABLE IF NOT EXISTS request_log(
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    route TEXT NOT NULL,                  -- API endpoint accessed
    status_code INT NOT NULL,             -- HTTP status code of the response
    latency_ms INT NOT NULL               -- Time taken to process the request in milliseconds
);
