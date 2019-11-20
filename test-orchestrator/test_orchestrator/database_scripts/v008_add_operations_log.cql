CREATE TABLE IF NOT EXISTS testtier.operation_log (
    timestamp timeuuid,
    test_id uuid,
    key text,
    op text,
    source text,
    target text,
    payload text,
    PRIMARY KEY (test_id, timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC);