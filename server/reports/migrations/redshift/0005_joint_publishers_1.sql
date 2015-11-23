CREATE VIEW joint_publishers_1 AS
SELECT 
	b1_publishers_1.date, 
	b1_publishers_1.adgroup_id, 
	b1_publishers_1.exchange, 
	b1_publishers_1.domain, 
	b1_publishers_1.clicks, 
	b1_publishers_1.impressions, 
	b1_publishers_1.cost_micro 
FROM b1_publishers_1 
UNION 
SELECT 
	ob_publishers_1.date, 
	ob_publishers_1.adgroup_id, 
	ob_publishers_1.exchange, 
	ob_publishers_1.domain, 
	ob_publishers_1.clicks, 
	ob_publishers_1.impressions, 
	ob_publishers_1.cost_micro 
FROM ob_publishers_1;
