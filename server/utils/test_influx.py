from django.test import TestCase

from utils import influx


class InfluxHelperTestCase(TestCase):

    def test_influx_incr(self):
        res = {}

        def incr(n, v):
            res['metric_name'] = n
            res['metric_value'] = v

        influx._telegraf_client.incr = incr
        influx._get_source = lambda: "my_host"

        influx.incr('test.metric', 2, source='my_source', tag='tag1')

        self.assertEqual(res, {'metric_name': 'test.metric,source=my_source,tag=tag1,host=my_host', 'metric_value': 2})

    def test_influx_gauge(self):
        res = {}

        def gauge(n, v):
            res['metric_name'] = n
            res['metric_value'] = v

        influx._telegraf_client.gauge = gauge
        influx._get_source = lambda: "h"

        influx.gauge('test.metric', 'v', source='my_source', tag='tag1')

        self.assertEqual(res, {'metric_name': 'test.metric,source=my_source,tag=tag1,host=h', 'metric_value': 'v'})

    def test_influx_block_timer(self):
        res = {}

        def timing(n, v):
            res['metric_name'] = n
            res['metric_value'] = v

        influx._telegraf_client.timing = timing
        influx._get_source = lambda: "h"

        with influx.block_timer("test.metric", source='my_source', tag='tag1'):
            pass

        self.assertEqual(res['metric_name'], 'test.metric,source=my_source,tag=tag1,host=h')

    def test_influx_decorator(self):
        res = {}

        def timing(n, v):
            res['metric_name'] = n
            res['metric_value'] = v

        influx._telegraf_client.timing = timing
        influx._get_source = lambda: "h"

        @influx.timer("test.metric", source='my_source', tag='tag1')
        def noop():
            pass

        noop()

        self.assertEqual(res['metric_name'], 'test.metric,source=my_source,tag=tag1,host=h')
