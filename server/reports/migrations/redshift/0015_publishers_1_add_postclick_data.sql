ALTER TABLE publishers_1 ADD COLUMN visits integer DEFAULT NULL;
ALTER TABLE publishers_1 ADD COLUMN new_visits integer DEFAULT NULL;
ALTER TABLE publishers_1 ADD COLUMN bounced_visits integer DEFAULT NULL;
ALTER TABLE publishers_1 ADD COLUMN pageviews integer DEFAULT NULL;
ALTER TABLE publishers_1 ADD COLUMN total_time_on_site integer DEFAULT NULL;
ALTER TABLE publishers_1 ADD COLUMN conversions varchar(2048) DEFAULT NULL;
