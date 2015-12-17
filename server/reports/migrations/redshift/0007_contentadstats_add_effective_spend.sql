ALTER TABLE contentadstats ADD COLUMN effective_cost_nano bigint DEFAULT NULL;
ALTER TABLE contentadstats ADD COLUMN effective_data_cost_nano bigint DEFAULT NULL;
ALTER TABLE contentadstats ADD COLUMN license_fee_nano bigint DEFAULT NULL;
