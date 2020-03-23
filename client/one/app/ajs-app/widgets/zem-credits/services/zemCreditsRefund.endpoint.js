var APP_CONFIG = require('../../../../app.config').APP_CONFIG;
var commonHelpers = require('../../../../shared/helpers/common.helpers');

angular
    .module('one.widgets')
    .service('zemCreditsRefundEndpoint', function($q, $http) {
        this.list = list;
        this.listAll = listAll;
        this.create = create;

        function list(creditId) {
            var url =
                APP_CONFIG.apiRestInternalUrl +
                '/credits/' +
                creditId +
                '/refunds/';

            // TODO (msuber): remove hack when credits
            // will use proper pagination solution!
            var params = {
                offset: '0',
                limit: '1000',
            };

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

        function listAll(agencyId, accountId) {
            var url = APP_CONFIG.apiRestInternalUrl + '/credits/refunds/';
            var params = getParams(agencyId, accountId);

            // TODO (msuber): remove hack when credits
            // will use proper pagination solution!
            params.offset = '0';
            params.limit = '1000';

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

        function create(creditId, creditRefundItem) {
            var url =
                APP_CONFIG.apiRestInternalUrl +
                '/credits/' +
                creditId +
                '/refunds/';

            var deferred = $q.defer();
            $http
                .post(url, convertCreditRefundItemToApi(creditRefundItem))
                .then(function(data) {
                    deferred.resolve(convertCreditItemFromApi(data.data.data));
                })
                .catch(function(error) {
                    deferred.reject(error);
                });

            return deferred.promise;
        }

        function getParams(agencyId, accountId) {
            var params = {};

            if (commonHelpers.isDefined(agencyId)) {
                params.agencyId = agencyId;
            }
            if (commonHelpers.isDefined(accountId)) {
                params.accountId = accountId;
            }

            return params;
        }

        function convertCreditItemFromApi(item) {
            item.createdOn = item.createdDt
                ? moment(item.createdDt, 'YYYY-MM-DD').format('MM/DD/YYYY')
                : null;
            item.startDate = item.startDate
                ? moment(item.startDate, 'YYYY-MM-DD').format('MM/DD/YYYY')
                : null;
            item.endDate = item.endDate
                ? moment(item.endDate, 'YYYY-MM-DD').format('MM/DD/YYYY')
                : null;
            return item;
        }

        function convertCreditRefundItemToApi(item) {
            item = angular.copy(item);

            if (commonHelpers.isDefined(item.startDate)) {
                item.startDate = moment(item.startDate).format('YYYY-MM-DD');
            }

            return item;
        }
    });
