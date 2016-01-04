CREATE VIEW joint_publishers_1_3 AS
SELECT 
	b1_publishers_1.date, 
	b1_publishers_1.adgroup_id, 
	b1_publishers_1.exchange, 
	b1_publishers_1.domain, 
	b1_publishers_1.clicks, 
	b1_publishers_1.impressions, 
	b1_publishers_1.cost_micro,
	b1_publishers_1.data_cost_micro,
	0 as license_fee_nano,
	0 as effective_cost_nano,
	0 as effective_data_cost_nano
FROM b1_publishers_1 
UNION 
SELECT 
	ob_publishers_2.date, 
	ob_publishers_2.adgroup_id, 
	ob_publishers_2.exchange, 
	ob_publishers_2.domain, 
	ob_publishers_2.clicks, 
	ob_publishers_2.impressions, 
	ob_publishers_2.cost_micro,
	0 as data_cost_micro,
	0 as license_fee_nano,
	0 as effective_cost_nano,
	0 as effective_data_cost_nano
FROM ob_publishers_2;
