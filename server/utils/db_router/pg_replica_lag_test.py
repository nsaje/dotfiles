from unittest import mock

from django.test import TestCase

from . import pg_replica_lag


class PGReplicaLagTest(TestCase):
    @mock.patch.object(pg_replica_lag, "_get_lag_from_db")
    def test_is_replica_healthy_true(self, mock_get_lag):
        mock_get_lag.return_value = pg_replica_lag.MAX_REPLICA_LAG - 5.0
        self.assertEqual(True, pg_replica_lag.is_replica_healthy("db1"))
        self.assertEqual(True, pg_replica_lag.is_replica_healthy("db1"))
        self.assertEqual(True, pg_replica_lag.is_replica_healthy("db2"))
        self.assertEqual(True, pg_replica_lag.is_replica_healthy("db2"))
        mock_get_lag.assert_has_calls([mock.call("db1"), mock.call("db2")])

    @mock.patch.object(pg_replica_lag, "_get_lag_from_db")
    def test_is_replica_healthy_false(self, mock_get_lag):
        mock_get_lag.return_value = pg_replica_lag.MAX_REPLICA_LAG + 5.0
        self.assertEqual(False, pg_replica_lag.is_replica_healthy("db3"))
        self.assertEqual(False, pg_replica_lag.is_replica_healthy("db3"))
        self.assertEqual(False, pg_replica_lag.is_replica_healthy("db4"))
        self.assertEqual(False, pg_replica_lag.is_replica_healthy("db4"))
        mock_get_lag.assert_has_calls([mock.call("db3"), mock.call("db4")])
