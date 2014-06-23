
import datetime
import random
import pprint

NETWORKS = [1, 2, 3, 4, 5]
AD_GROUPS = range(1, 11)

N_ARTICLES = range(1, 11)

START_DATE = datetime.date(2014, 5, 1)
END_DATE = datetime.date(2014, 7, 1)

DATE_DELTA = range(30)

IN_N_NETWORKS = range(1, len(NETWORKS) + 1)

def create_fake_data():
    base_aid = 1
    rows = []
    for ad_group in AD_GROUPS:
        #print ad_group
        random.shuffle(N_ARTICLES)
        n_articles = random.choice(N_ARTICLES)
        random.shuffle(IN_N_NETWORKS)
        n_networks = random.choice(IN_N_NETWORKS)
        random.shuffle(NETWORKS)
        networks = NETWORKS[:n_networks]
        random.shuffle(DATE_DELTA)
        start_date = START_DATE + datetime.timedelta(days=random.choice(DATE_DELTA))
        dates = [start_date]
        cpc = random.lognormvariate(2.5, 1) / 100
        while dates[-1] < END_DATE:
            dates.append(dates[-1] + datetime.timedelta(days=1))

        for i in range(n_articles):
            aid = base_aid + i
            for dt in dates:
                #print dt
                for network in networks:
                    imps = int(random.lognormvariate(6, 2))
                    ctr = random.betavariate(5, 395)
                    clicks = int(imps * ctr)
                    cost = clicks * cpc

                    row = {
                        'date': dt,
                        'article': aid,
                        'ad_group': ad_group,
                        'network': network,
                        'impressions': imps,
                        'clicks': clicks,
                        'cost': cost,
                        'cpc': cpc,
                    }

                    rows.append(row)

        base_aid = base_aid + n_articles
        rows = sorted(rows, key=lambda x: (x['date'], x['ad_group'], x['network'], x['article']))
    return rows


if __name__ == '__main__':
    data = create_fake_data()
    print 'import datetime\n'
    print 'DATA = ['
    for row in data:
        print row, ','
    print ']'






