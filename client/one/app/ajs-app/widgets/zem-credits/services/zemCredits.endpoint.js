var APP_CONFIG = require('../../../../app.config').APP_CONFIG;
var commonHelpers = require('../../../../shared/helpers/common.helpers');
var CreditStatus = require('../../../../app.constants').CreditStatus;

angular
    .module('one.widgets')
    .service('zemCreditsEndpoint', function($q, $http, config) {
        this.totals = totals;
        this.listActive = listActive;
        this.listPast = listPast;
        this.listBudgets = listBudgets;
        this.create = create;
        this.update = update;

        function totals(agencyId, accountId) {
            var url = APP_CONFIG.apiRestInternalUrl + '/credits/totals/';
            var params = getParams(agencyId, accountId);

            var deferred = $q.defer();
            $http
                .get(url, {params: params})
                .then(function(data) {
                    deferred.resolve(
                        data.data.data.map(convertCreditTotalsFromApi)
                    );
                })
                .catch(function(error) {
                    deferred.reject(error);
                });

            return deferred.promise;
        }

        function listActive(agencyId, accountId) {
            return list(agencyId, accountId, true);
        }

        function listPast(agencyId, accountId) {
            return list(agencyId, accountId, false);
        }

        function list(agencyId, accountId, active) {
            var url = APP_CONFIG.apiRestInternalUrl + '/credits/';
            var params = getParams(agencyId, accountId, active);

            var deferred = $q.defer();
            $http
                .get(url, {params: params})
                .then(function(data) {
                    deferred.resolve(
                        data.data.data.map(convertCreditItemFromApi)
                    );
                })
                .catch(function(error) {
                    deferred.reject(error);
                });

            return deferred.promise;
        }

        function listBudgets(creditId) {
            var url =
                APP_CONFIG.apiRestInternalUrl +
                '/credits/' +
                creditId +
                '/budgets/';

            var deferred = $q.defer();
            $http
                .get(url)
                .then(function(data) {
                    deferred.resolve(
                        data.data.data.map(convertBudgetItemFromApi)
                    );
                })
                .catch(function(error) {
                    deferred.reject(error);
                });

            return deferred.promise;
        }

        function create(creditItem) {
            var url = APP_CONFIG.apiRestInternalUrl + '/credits/';

            var deferred = $q.defer();
            $http
                .post(url, convertCreditItemToApi(creditItem))
                .then(function(data) {
                    deferred.resolve(convertCreditItemFromApi(data.data.data));
                })
                .catch(function(error) {
                    deferred.reject(error);
                });

            return deferred.promise;
        }

        function update(creditItem) {
            var url =
                APP_CONFIG.apiRestInternalUrl + '/credits/' + creditItem.id;

            var deferred = $q.defer();
            $http
                .put(url, convertCreditItemToApi(creditItem))
                .then(function(data) {
                    deferred.resolve(convertCreditItemFromApi(data.data.data));
                })
                .catch(function(error) {
                    deferred.reject(error);
                });

            return deferred.promise;
        }

        function getParams(agencyId, accountId, active) {
            var params = {};

            if (commonHelpers.isDefined(agencyId)) {
                params.agencyId = agencyId;
            }
            if (commonHelpers.isDefined(accountId)) {
                params.accountId = accountId;
            }
            if (commonHelpers.isDefined(active)) {
                params.active = active;
            }

            return params;
        }

        function convertCreditTotalsFromApi(totals) {
            totals.currencySymbol = config.currencySymbols[totals.currency];
            return totals;
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
            item.currencySymbol = APP_CONFIG.currencySymbols[item.currency];
            item.isSigned = item.status === CreditStatus.SIGNED;
            item.isCanceled = item.status === CreditStatus.CANCELED;
            return item;
        }

        function convertCreditItemToApi(item) {
            item = angular.copy(item);

            item.startDate = moment(item.startDate).format('YYYY-MM-DD');
            item.endDate = moment(item.endDate).format('YYYY-MM-DD');

            if (
                commonHelpers.getValueOrDefault(item.isSigned, false) &&
                item.status === CreditStatus.PENDING
            ) {
                item.status = CreditStatus.SIGNED;
            }

            return item;
        }

        function convertBudgetItemFromApi(item) {
            item.startDate = item.startDate
                ? moment(item.startDate, 'YYYY-MM-DD').format('MM/DD/YYYY')
                : null;
            item.endDate = item.endDate
                ? moment(item.endDate, 'YYYY-MM-DD').format('MM/DD/YYYY')
                : null;
            return item;
        }
    });
