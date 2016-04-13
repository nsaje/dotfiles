import backtosql
from backtosql import Model, Column, TemplateColumn
import time
from functools import partial
import json
import collections
import threading
from multiprocessing.pool import ThreadPool
from django.conf import settings
from django.db import connections


PRINTSQL = True

class ColumnGroup(object):
    BREAKDOWN = 1
    AGGREGATES = 2

CGB = ColumnGroup.BREAKDOWN
CGA = ColumnGroup.AGGREGATES


SumColumn = partial(TemplateColumn, 'part_sum.sql', group=CGA)

class RSHamaxModel(Model):
    dt = TemplateColumn('part_trunc_date.sql', {'column_name': 'dt'}, group=CGB)

    exchange = Column('exchange', group=CGB)
    content_ad_id = Column('content_ad_id', group=CGB)
    ad_group_id = Column('ad_group_id', group=CGB)
    publisher = Column('publisher', group=CGB)

    device_type = Column('device_type', group=CGB)
    country = Column('country', group=CGB)
    state = Column('state', group=CGB)
    dma = Column('dma', group=CGB)
    age = Column('age', group=CGB)
    gender = Column('gender', group=CGB)

    clicks = SumColumn(context={'column_name': 'clicks'})
    wins = SumColumn(context={'column_name': 'wins'})
    spend = SumColumn(context={'column_name': 'spend'})
    data_spend = SumColumn(context={'column_name': 'data_spend'})

import datetime
C_L1 = {
    'ad_group_id': [890, 1349, 1172, 1343, 1170, 1169, 885, 1411],
    'date_from': datetime.date(2016, 1, 1),
    'date_to': datetime.date(2016, 2, 20)}
C_L3C = {
    'ad_group_id': [890, 1349, 1172, 1343, 1170, 1169, 885, 1411],
    'content_ad_id': [52901,167150,167167,167170,167222,55283,55289,55316,167296,167319,114043,170893,170900,170907,170912,170916,170924,170929,170932,170934,170348,170349,170350,170355,170356],
    'date_from': datetime.date(2016, 1, 1),
    'date_to': datetime.date(2016, 2, 20)}
C_L4C = {
    'ad_group_id': [890, 1349, 1172, 1343, 1170, 1169, 885, 1411],
    'content_ad_id': [52901,167150,167167,167170,167222,55283,55289,55316,167296,167319,114043,170893,170900,170907,170912,170916,170924,170929,170932,170934,170348,170349,170350,170355,170356],
    'date_from': datetime.date(2016, 1, 10),
    'date_to': datetime.date(2016, 1, 15)}
C_L3P = {
    'ad_group_id': [890, 1349, 1172, 1343, 1170, 1169, 885, 1411],
    'publisher': ['airstream.littlethings.com','dodge-dart.org','organizingmadefun.blogspot.ca','vernalalisasrecipeboard.yuku.com','wolfslair33820.yuku.com','3yummytummies.com','Tagged MoPub Android','alteredgamer.com','antfarm.yuku.com','atlnightspots.com','aww.buzzlie.com','bridaltune.com','charismamag.com','classmates.com','conferencecalltranscripts.org','aggieskitchen.com','bestmealintheworld.com','kdramastars.com','legacy.newsok.com','oakbaynews.com','androidcentral.com','castlegarnews.com','m.eonline.com','obituaries.galesburg.com','outdoorlife.com'],
    'date_from': datetime.date(2016, 1, 1),
    'date_to': datetime.date(2016, 2, 20)}
C_L4P = {
    'ad_group_id': [890, 1349, 1172, 1343, 1170, 1169, 885, 1411],
    'publisher': ['airstream.littlethings.com','dodge-dart.org','organizingmadefun.blogspot.ca','vernalalisasrecipeboard.yuku.com','wolfslair33820.yuku.com','3yummytummies.com','Tagged MoPub Android','alteredgamer.com','antfarm.yuku.com','atlnightspots.com','aww.buzzlie.com','bridaltune.com','charismamag.com','classmates.com','conferencecalltranscripts.org','aggieskitchen.com','bestmealintheworld.com','kdramastars.com','legacy.newsok.com','oakbaynews.com','androidcentral.com','castlegarnews.com','m.eonline.com','obituaries.galesburg.com','outdoorlife.com'],
    'date_from': datetime.date(2016, 1, 10),
    'date_to': datetime.date(2016, 1, 15)}
C_K1 = {
    'ad_group_id': [890],
    'date_from': datetime.date(2016, 1, 1),
    'date_to': datetime.date(2016, 2, 20)}

C_K3E = {
    'ad_group_id': [890],
    'content_ad_id': [55240,55264,163269,167310,167314,167315,167317,167277,167303,167324,167331,55291,167274,167275,167347,55250,55285,55248,55316,167332,55262,55266,55230,55232,55303,167284,167338,167340,167269,167299,167330],
    'date_from': datetime.date(2016, 1, 1),
    'date_to': datetime.date(2016, 2, 20)}
C_K4E = {
    'ad_group_id': [890],
    'content_ad_id': [55240,55264,163269,167310,167314,167315,167317,167277,167303,167324,167331,55291,167274,167275,167347,55250,55285,55248,55316,167332,55262,55266,55230,55232,55303,167284,167338,167340,167269,167299,167330],
    'date_from': datetime.date(2016, 1, 10),
    'date_to': datetime.date(2016, 1, 15)}
C_K3P = {
    'ad_group_id': [890],
    'content_ad_id': [55240,55264,163269,167310,167314,167315,167317,167277,167303,167324,167331,55291,167274,167275,167347,55250,55285,55248,55316,167332,55262,55266,55230,55232,55303,167284,167338,167340,167269,167299,167330],
    'publisher': ['dose.com','lifedaily.com','littlethings.com','m.en.softonic.com','thefoodcharlatan.com','1000lifehacks.com','bocalista.com','thesportbuzz.com','wideopencountry.com','z420.tv','allrecipes.com','kcentv.com','thesportbuzz.com','univision.com','womansworldmag.com','ctsvowners.com','dynomove.com','filmshout.com','leitesculinaria.com','veryhangry.com','aplus.com','crazyprank.com','dailyquenchers.com','dogster.com','m.activebeat.com'],
    'date_from': datetime.date(2016, 1, 1),
    'date_to': datetime.date(2016, 2, 20)}
C_K4P = {
    'ad_group_id': [890],
    'content_ad_id': [55240,55264,163269,167310,167314,167315,167317,167277,167303,167324,167331,55291,167274,167275,167347,55250,55285,55248,55316,167332,55262,55266,55230,55232,55303,167284,167338,167340,167269,167299,167330],
    'publisher': ['dose.com','lifedaily.com','littlethings.com','m.en.softonic.com','thefoodcharlatan.com','1000lifehacks.com','bocalista.com','thesportbuzz.com','wideopencountry.com','z420.tv','allrecipes.com','kcentv.com','thesportbuzz.com','univision.com','womansworldmag.com','ctsvowners.com','dynomove.com','filmshout.com','leitesculinaria.com','veryhangry.com','aplus.com','crazyprank.com','dailyquenchers.com','dogster.com','m.activebeat.com'],
    'date_from': datetime.date(2016, 1, 10),
    'date_to': datetime.date(2016, 1, 15)}

breakdowns = {
    'L1': (['ad_group_id'], 'a_adgs', C_L1),
    'L2C': (['ad_group_id', 'content_ad_id'], 'a_adg_cads', C_L1),
    'L3C': (['ad_group_id', 'content_ad_id', 'dma'], 'a_adg_cads_extra', C_L3C),
    'L4C': (['ad_group_id', 'content_ad_id', 'dma', 'dt'], 'a_adg_cads_extra', C_L4C),
    'L2P': (['ad_group_id', 'publisher'], 'a_adg_pubs', C_L1),
    'L3P': (['ad_group_id', 'publisher', 'dma'], 'a_adg_pubs_extra', C_L3P),
    'L4P': (['ad_group_id', 'publisher', 'dma', 'dt'], 'a_adg_pubs_extra', C_L4P),

    'K1': (['content_ad_id'], 'a_adg_cads', C_K1),
    'K2E': (['content_ad_id', 'exchange'], 'a_adg_cads_exc', C_K1),
    'K3E': (['content_ad_id', 'exchange', 'dma'], 'a_adg_cads_exc_extra', C_K3E),
    'K4E': (['content_ad_id', 'exchange', 'dma', 'dt'], 'a_adg_cads_exc_extra', C_K4E),
    'K2P': (['content_ad_id', 'publisher'], 'a_adg_cads_pubs', C_K1),
    'K3P': (['content_ad_id', 'publisher', 'dma'], 'a_adg_cads_pubs_extra', C_K3P),
    'K4P': (['content_ad_id', 'publisher', 'dma', 'dt'], 'a_adg_cads_pubs_extra', C_K4P),
}

from redshift import db
def get_cursor():
    return db.RSCursor()


def ex(q, constraints, cursor):
    total = None
    t = time.time()
    q = cursor.mogrify(q, constraints)
    cursor.execute(q, None)
    if PRINTSQL:
        print q
    return time.time() - t

def gen_q(breakdown_key):
    template_name = 'bench_l1.sql' if ('1' in breakdown_key or '4' in breakdown_key) else 'bench_l2.sql'

    constraints = breakdowns[breakdown_key][2]
    breakdown = breakdowns[breakdown_key][0]

    view = breakdowns[breakdown_key][1]
    breakdowns_c = RSHamaxModel.select_columns(subset=breakdown)
    aggregates_c = RSHamaxModel.select_columns(group=CGA)
    group_size = 5

    sql = backtosql.generate_sql(template_name, {
        'view': view,
        'breakdown': breakdowns_c,
        'aggregates': aggregates_c,
        'group_size': group_size,
        'total_size': group_size ** len(breakdowns_c)
    })

    return sql

def execute_breakdown(cursor, breakdown_key):
    sql = gen_q(breakdown_key)
    constraints = breakdowns[breakdown_key][2]

    return ex(sql, constraints, cursor)


def warmup():
    res = {}
    PRINTSQL = True
    with get_cursor() as c:
        for k in breakdowns.keys():
            with get_cursor() as c:
                res[k] = execute_breakdown(c, k)
            print k, res[k]
    PRINTSQL = False
    print json.dumps(res, sort_keys=True, indent=4)


def doit(nr_each=3):
    print 'WORKER'
    res = collections.defaultdict(list)
    for k in breakdowns.keys():
        times = res[k]
        times_c = []
        for i in range(nr_each):
            tc = time.time()

            with get_cursor() as c:
                times.append(execute_breakdown(c, k))

            times_c.append(time.time() - tc - times[-1])

            print k, times[-1], times_c[-1]

        times.append(reduce(lambda a, b: a + b, times) / len(times))
        times_c.append(reduce(lambda a, b: a + b, times_c) / len(times_c))

        print 'AVG', k, times[-1], times_c[-1]

    return res

def doitparallel(cl, nr_users=5):
    final = {}
    for nr in range(1, nr_users + 1):
        pool = ThreadPool(processes=nr)

        res = []
        for x in range(nr):
            pool.apply_async(doit, callback=res.append)
        pool.close()
        pool.join()

        print json.dumps({'result_{}'.format(nr): res}, sort_keys=True, indent=4)
        final['result_{}'.format(nr)] = res

        time.sleep(1)

    with open('rs_test_clusters_{}'.format(cl), 'w') as ws:
        json.dump(final, ws, sort_keys=True, indent=4)

