import backtosql


class Inventory(backtosql.Model):
    country = backtosql.Column('country', group=1)
    publisher = backtosql.Column('publisher', group=1)
    device_type = backtosql.Column('device_type', group=1)

    bid_reqs = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'bid_reqs'}, group=2)
    bids = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'bids'}, group=2)
    win_notices = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'win_notices'}, group=2)
    total_win_price = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'total_win_price'}, group=2)
