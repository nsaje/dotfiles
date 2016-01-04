create table ob_publishers_2(
        date date not null,
        adgroup_id integer not null,
        exchange varchar(255),
        domain varchar(255),
        name varchar(255),
        clicks int,
        impressions int,  
        cost_micro bigint,
        ob_id varchar(255),
        unique (date, adgroup_id, exchange, domain))
sortkey(date, adgroup_id);
