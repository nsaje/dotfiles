var ActionTopic = require('../../../../workers/shared/workers.constants')
    .ActionTopic;

angular
    .module('one.services')
    .service('zemNavigationLegacyEndpoint', function(
        $q,
        $http,
        zemDataFilterService,
        zemWorkersService
    ) {
        this.get = get;
        this.list = list;
        this.getAdGroup = getAdGroup;
        this.getCampaign = getCampaign;
        this.getAccount = getAccount;
        this.getAccountsAccess = getAccountsAccess;

        function getAdGroup(id) {
            return get('ad_groups/' + id);
        }

        function getCampaign(id) {
            return get('campaigns/' + id);
        }

        function getAccount(id) {
            return get('accounts/' + id);
        }

        function getAccountsAccess() {
            return get('all_accounts');
        }

        function get(route) {
            var deferred = $q.defer();
            var url = '/api/' + route + '/nav/';
            var config = {
                params: {},
            };
            addFilteredSources(config.params);
            addAgencyFilter(config.params);
            addAccountTypeFilter(config.params);

            $http
                .get(url, config)
                .success(function(data) {
                    var resource;

                    if (data && data.data) {
                        resource = data.data;
                    }
                    deferred.resolve(convertFromApi(resource));
                })
                .error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }

        function list(omitStatuses) {
            var deferred = $q.defer();
            var url = '/api/nav/';
            if (omitStatuses) {
                url += '?loadStatuses=false';
            }
            var config = {
                params: {},
            };
            addFilteredSources(config.params);
            addAgencyFilter(config.params);
            addAccountTypeFilter(config.params);

            // Angular.js $http client by default uses JSON.parse to transform incoming response data.
            // Parsing huge response can block the main ui thread.
            // SOURCE: https://github.com/angular/angular.js/blob/3a3db690a16e888aa7371e3b02e2954b9ec2d558/src/ng/http.js#L241
            // SOLUTION: use web worker to fetch and parse response data.

            zemWorkersService
                .runWorker(ActionTopic.FETCH_NAVIGATION, {
                    url: window.location.origin + url,
                })
                .then(function(data) {
                    var resource;
                    if (data && data.data) {
                        resource = data.data;
                    }
                    deferred.resolve(resource || []);
                })
                .catch(function() {
                    $http
                        .get(url, config)
                        .success(function(data) {
                            var resource;
                            if (data && data.data) {
                                resource = data.data;
                            }
                            deferred.resolve(resource || []);
                        })
                        .error(function(data) {
                            deferred.reject(data);
                        });
                });

            return deferred.promise;
        }

        function convertFromApi(models) {
            if (!models) return;

            if (models.hasOwnProperty('ad_group')) {
                models.adGroup = models.ad_group;
                delete models.ad_group;
            }

            if (models.hasOwnProperty('accounts_count')) {
                models.accountsCount = models.accounts_count;
                delete models.accounts_count;
                models.hasAccounts = models.accountsCount > 0;
            }

            if (models.hasOwnProperty('default_account_id')) {
                models.defaultAccountId = models.default_account_id;
                delete models.default_account_id;
            }

            return models;
        }

        function addFilteredSources(params) {
            var filteredSources = zemDataFilterService.getFilteredSources();
            if (filteredSources.length > 0) {
                params.filtered_sources = filteredSources.join(',');
            }
        }

        function addAgencyFilter(params) {
            var filteredAgencies = zemDataFilterService.getFilteredAgencies();
            if (filteredAgencies.length > 0) {
                params.filtered_agencies = filteredAgencies;
            }
        }

        function addAccountTypeFilter(params) {
            var filteredAccountTypes = zemDataFilterService.getFilteredAccountTypes();
            if (filteredAccountTypes.length > 0) {
                params.filtered_account_types = filteredAccountTypes;
            }
        }
    });
