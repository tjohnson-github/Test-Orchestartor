CREATE TABLE IF NOT EXISTS testtier.usageraw (
    date timestamp,
    test_id uuid,
    session_id text,
    source text,
    upload_WifiTCP int,
    upload_WifiUDP int,
    upload_CellTCP int,
    upload_CellUDP int,
    download_WifiTCP int,
    download_WifiUDP int,
    download_CellTCP int,
    download_CellUDP int,
    timestamp_value int,
    timestamp_units text,
    raw_json text,
    PRIMARY KEY (test_id, date)
) WITH CLUSTERING ORDER BY (date DESC);

