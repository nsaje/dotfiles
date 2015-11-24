create table b1_publishers_1(
        date date not null,
        adgroup_id integer not null,
        exchange varchar(255),
        domain varchar(255),
        clicks int,
        impressions int,  
        cost_micro bigint,
        data_cost_micro bigint,
        unique (date, adgroup_id, exchange, domain))
sortkey(date, adgroup_id);
