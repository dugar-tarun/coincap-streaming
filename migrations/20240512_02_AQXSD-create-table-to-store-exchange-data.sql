-- Create table to store exchange data
-- depends: 20240512_01_9IE3b-create-schema-for-the-database

CREATE TABLE IF NOT EXISTS bitcoin_exchange.exchange
(
    id VARCHAR(50),
    name VARCHAR(50),
    rank INT,
    percentTotalVolume NUMERIC(8, 5),
    volumeUsd NUMERIC(18, 5),
    tradingPairs INT,
    socket BOOLEAN,
    exchangeUrl VARCHAR(50),
    updated_unix_millis BIGINT,
    updated_utc TIMESTAMP
)
