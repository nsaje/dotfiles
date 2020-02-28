var ScopeSelectorState = require('../../../shared/components/scope-selector/scope-selector.constants')
    .ScopeSelectorState;

angular
    .module('one.widgets')
    .service('zemPublisherGroupsEndpoint', function($q, $http, $window) {
        this.list = list;
        this.download = download;
        this.upsert = upsert;
        this.downloadErrors = downloadErrors;
        this.downloadExample = downloadExample;

        function list(accountId, agencyId, notImplicit) {
            var url = '/api/accounts/' + accountId + '/publisher_groups/';
            var config = {
                params: {
                    not_implicit: notImplicit,
                },
            };

            var deferred = $q.defer();
            $http
                .get(url, config)
                .then(function(data) {
                    deferred.resolve(data.data.data.publisher_groups);
                })
                .catch(function(data) {
                    deferred.reject(data);
                });
            return deferred.promise;
        }

        function download(accountId, agencyId, publisherGroupId) {
            var url =
                '/api/accounts/' +
                accountId +
                '/publisher_groups/' +
                publisherGroupId +
                '/download/';
            $window.open(url, '_blank');
        }

        function upsert(data) {
            var deferred = $q.defer();
            var url =
                '/api/accounts/' + data.accountId + '/publisher_groups/upload/';

            var formData = new FormData();
            formData.append('name', data.name);
            formData.append('entries', data.file);

            if (data.include_subdomains) {
                formData.append('include_subdomains', data.include_subdomains);
            }

            if (data.id) {
                formData.append('id', data.id);
            }

            if (
                data.scopeState === ScopeSelectorState.AGENCY_SCOPE &&
                data.agencyId
            ) {
                formData.append('agency_id', data.agencyId);
            } else if (
                data.scopeState === ScopeSelectorState.ACCOUNT_SCOPE &&
                data.accountId
            ) {
                formData.append('account_id', data.accountId);
            }

            $http
                .post(url, formData, {
                    transformRequest: angular.identity,
                    headers: {'Content-Type': undefined},
                })
                .then(function(data) {
                    deferred.resolve(data.data);
                })
                .catch(function(data) {
                    if (status === '413') {
                        data = {
                            data: {
                                errors: {
                                    entries: ['File too large (max 1MB).'],
                                },
                            },
                            success: false,
                        };
                    }
                    deferred.reject(data.data.data.errors);
                });

            return deferred.promise;
        }

        function downloadErrors(accountId, agencyId, csvKey) {
            var url =
                '/api/accounts/' +
                accountId +
                '/publisher_groups/errors/' +
                csvKey;
            $window.open(url, '_blank');
        }

        function downloadExample() {
            var url = '/api/publisher_groups/download/example/';
            $window.open(url, '_blank');
        }
    });
