angular
    .module('one.widgets')
    .service('zemAccountCreditRefundEndpoint', function($q, $http, zemUtils) {
        this.list = list;
        this.create = create;

        function list(accountId) {
            var url =
                '/rest/internal/accounts/' + accountId + '/credit/refunds/';

            var deferred = $q.defer();
            $http
                .get(url)
                .then(function(data) {
                    deferred.resolve(
                        convertCreditRefundsListFromApi(
                            zemUtils.convertToCamelCase(data.data.data)
                        )
                    );
                })
                .catch(function(error) {
                    deferred.reject(error);
                });

            return deferred.promise;
        }

        function create(accountId, creditId, item) {
            var url =
                '/rest/internal/accounts/' +
                accountId +
                '/credit/' +
                creditId +
                '/refunds/';
            var deferred = $q.defer();
            $http
                .post(
                    url,
                    zemUtils.convertToUnderscore(
                        convertCreditRefundItemToApi(item)
                    )
                )
                .then(function(data) {
                    deferred.resolve(data.data.data);
                })
                .catch(function(error) {
                    deferred.reject(
                        zemUtils.convertToCamelCase(
                            convertErrorsFromApi(error.data.details)
                        )
                    );
                });

            return deferred.promise;
        }

        function convertCreditRefundsListFromApi(data) {
            return data.map(convertCreditItemFromApi);
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
            if (item.startDate) {
                item.startDate = moment(item.startDate).format('YYYY-MM-DD');
            }
            return item;
        }

        function convertErrorsFromApi(errors) {
            errors.status = errors.__all__;
            delete errors.__all__;
            return errors;
        }
    });
