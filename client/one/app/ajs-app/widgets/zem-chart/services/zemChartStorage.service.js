angular
    .module('one')
    .service('zemChartStorageService', function(
        zemLocalStorageService,
        zemNavigationNewService
    ) {
        this.loadMetrics = loadMetrics;
        this.saveMetrics = saveMetrics;

        var LOCAL_STORAGE_NAMESPACE = 'zemChart';
        var ALL_ACCOUNTS_KEY = 'allAccounts';
        var KEY_METRICS = 'metrics';

        function loadMetrics(level) {
            var accountKey = getAccountKey(
                level,
                zemNavigationNewService.getActiveAccount()
            );
            var storedMetrics =
                zemLocalStorageService.get(
                    KEY_METRICS,
                    LOCAL_STORAGE_NAMESPACE
                ) || {};
            return storedMetrics[accountKey];
        }

        function saveMetrics(metrics, level) {
            var accountKey = getAccountKey(
                level,
                zemNavigationNewService.getActiveAccount()
            );
            var storedMetrics =
                zemLocalStorageService.get(
                    KEY_METRICS,
                    LOCAL_STORAGE_NAMESPACE
                ) || {};
            storedMetrics[accountKey] = metrics;
            zemLocalStorageService.set(
                KEY_METRICS,
                storedMetrics,
                LOCAL_STORAGE_NAMESPACE
            );
        }

        function getAccountKey(level, activeAccount) {
            if (level === constants.level.ALL_ACCOUNTS) {
                return ALL_ACCOUNTS_KEY;
            } else if (activeAccount) {
                return activeAccount.id.toString();
            }
        }
    });
