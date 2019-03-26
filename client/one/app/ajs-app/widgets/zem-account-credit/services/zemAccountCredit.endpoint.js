angular
    .module('one.widgets')
    .service('zemAccountCreditEndpoint', function($q, $http, zemUtils, config) {
        this.list = list;
        this.create = create;
        this.update = update;
        this.get = get;
        this.cancel = cancel;

        function list(accountId) {
            var url = '/api/accounts/' + accountId + '/credit/';

            var deferred = $q.defer();
            $http
                .get(url)
                .then(function(data) {
                    deferred.resolve(
                        convertCreditListFromApi(
                            zemUtils.convertToCamelCase(data.data.data)
                        )
                    );
                })
                .catch(function(error) {
                    deferred.reject(error);
                });

            return deferred.promise;
        }

        function create(accountId, item) {
            var url = '/api/accounts/' + accountId + '/credit/';

            var deferred = $q.defer();
            $http
                .put(
                    url,
                    zemUtils.convertToUnderscore(convertCreditItemToApi(item))
                )
                .then(function(data) {
                    deferred.resolve(data.data.data);
                })
                .catch(function(error) {
                    deferred.reject(
                        zemUtils.convertToCamelCase(
                            convertErrorsFromApi(error.data.data.errors)
                        )
                    );
                });

            return deferred.promise;
        }

        function update(accountId, item) {
            var url = '/api/accounts/' + accountId + '/credit/' + item.id + '/';

            var deferred = $q.defer();
            $http
                .post(
                    url,
                    zemUtils.convertToUnderscore(convertCreditItemToApi(item))
                )
                .then(function(data) {
                    deferred.resolve(data.data.data);
                })
                .catch(function(error) {
                    deferred.reject(
                        zemUtils.convertToCamelCase(
                            convertErrorsFromApi(error.data.data.errors)
                        )
                    );
                });

            return deferred.promise;
        }

        function get(accountId, itemId) {
            var url = '/api/accounts/' + accountId + '/credit/' + itemId + '/';

            var deferred = $q.defer();
            $http
                .get(url)
                .then(function(data) {
                    deferred.resolve(
                        convertCreditItemFromApi(
                            zemUtils.convertToCamelCase(data.data.data)
                        )
                    );
                })
                .catch(function(error) {
                    deferred.reject(error);
                });

            return deferred.promise;
        }

        function cancel(accountId, itemIds) {
            var url = '/api/accounts/' + accountId + '/credit/';

            var deferred = $q.defer();
            $http
                .post(url, {cancel: itemIds})
                .then(function(data) {
                    deferred.resolve(data.data.data);
                })
                .catch(function(error) {
                    deferred.reject(error);
                });

            return deferred.promise;
        }

        function convertCreditListFromApi(data) {
            return {
                active: (data.active || []).map(convertCreditItemFromApi),
                past: (data.past || []).map(convertCreditItemFromApi),
                totals: convertCreditTotalsFromApi(data.totals),
            };
        }

        function convertCreditItemFromApi(item) {
            item.createdOn = item.createdOn
                ? moment(item.createdOn, 'YYYY-MM-DD').format('MM/DD/YYYY')
                : null;
            item.startDate = item.startDate
                ? moment(item.startDate, 'YYYY-MM-DD').format('MM/DD/YYYY')
                : null;
            item.endDate = item.endDate
                ? moment(item.endDate, 'YYYY-MM-DD').format('MM/DD/YYYY')
                : null;
            item.currencySymbol = config.currencySymbols[item.currency];

            item.budgets = (item.budgets || []).map(function(budget) {
                budget.startDate = budget.startDate
                    ? moment(budget.startDate, 'YYYY-MM-DD').format(
                          'MM/DD/YYYY'
                      )
                    : null;
                budget.endDate = budget.endDate
                    ? moment(budget.endDate, 'YYYY-MM-DD').format('MM/DD/YYYY')
                    : null;
                budget.currencySymbol = config.currencySymbols[budget.currency];
                return budget;
            });
            item.numOfBudgets = (item.budgets || []).length;

            return item;
        }

        function convertCreditTotalsFromApi(totals) {
            totals.currencySymbol = config.currencySymbols[totals.currency];
            return totals;
        }

        function convertCreditItemToApi(item) {
            item.startDate = moment(item.startDate).format('YYYY-MM-DD');
            item.endDate = moment(item.endDate).format('YYYY-MM-DD');

            return item;
        }

        function convertErrorsFromApi(errors) {
            errors.status = errors.__all__;
            delete errors.__all__;
            return errors;
        }
    });
