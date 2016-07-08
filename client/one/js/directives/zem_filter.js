/*global $,oneApp,constants*/
'use strict';

oneApp.directive('zemFilter', ['config', function (config) {
    return {
        restrict: 'E',
        templateUrl: '/partials/zem_filter.html',
        scope: {
            hasPermission: '=zemHasPermission',
            isPermissionInternal: '=zemIsPermissionInternal',
            enablePublisherFilter: '=enablePublisherFilter ',
            showPublisherSelected: '=showPublisherSelected',
        },
        link: function ($scope, element) {
            element.on('click', function (e) {
                e.stopPropagation();
            });
        },
        controller: ['$scope', '$state', '$rootScope', 'zemFilterService', 'zemUserSettings', 'api', function ($scope, $state, $rootScope, zemFilterService, zemUserSettings, api) {
            $scope.availableSources = [];
            $scope.agencies = [];
            $scope.config = config;
            $scope.enablePublisherFilter = false;
            $scope.showPublisherSelected = 'all';
            $scope.accountTypes = [];
            $scope.agencyFilterVisible = false;
            $scope.accountTypeFilterVisible = false;
            $scope.refreshAvailableSources = function () {
                api.availableSources.list().then(function (data) {
                    $scope.availableSources = data.data.sources;
                });
            };

            $scope.refreshAgencies = function () {
                api.agencies.list().then(function (data) {
                    $scope.agencies = data.data.agencies;
                });
            };

            $scope.refreshAccountTypes = function () {
                $scope.accountTypes = constants.defaultAccountTypes;
            };

            $scope.addFilteredSource = function (sourceId) {
                if (!sourceId || sourceId === '') {
                    return;
                }

                zemFilterService.addFilteredSource(sourceId);
                $scope.sourceIdToFilter = '';
            };

            $scope.exclusivelyFilterSource = function (sourceId) {
                zemFilterService.exclusivelyFilterSource(sourceId);
            };

            $scope.isSourceFiltered = function (source) {
                return zemFilterService.isSourceFiltered(source.id);
            };

            $scope.isSourceValidFilterChoice = function (source) {
                return !$scope.isSourceFiltered(source) && !$scope.isSourceDeprecated(source);
            };

            $scope.isAgencyValidFilterChoice = function (agency) {
                return !$scope.isAgencyFiltered(agency);
            }

            $scope.isAccountTypeValidFilterChoice = function (accountType) {
                return !$scope.isAccountTypeFiltered(accountType);
            }

            $scope.isSourceDeprecated = function (source) {
                return source.deprecated;
            };

            $scope.isSourceNotFiltered = function (source) {
                return !$scope.isSourceFiltered(source);
            };

            $scope.isFilterOn = function () {
                return zemFilterService.isSourceFilterOn() || 
                    zemFilterService.isAgencyFilterOn() ||
                    zemFilterService.isAccountTypeFilterOn() ||
                    zemFilterService.isPublisherBlacklistFilterOn();
            };

            $scope.removeFiltering = function () {
                zemFilterService.removeFiltering();
            };

            $scope.removeFilteredSource = function (sourceId) {
                zemFilterService.removeFilteredSource(sourceId);
            };

            $scope.isAgencyFiltered = function (agency) {
                return zemFilterService.isAgencyFiltered(agency.id);
            };

            $scope.addFilteredAgency = function (agencyId) {
                if (!agencyId || agencyId === '') {
                    return;
                }

                zemFilterService.addFilteredAgency(agencyId);
                $scope.agencyIdToFilter = '';
            };

            $scope.removeFilteredAgency = function (agencyId) {
                zemFilterService.removeFilteredAgency(agencyId);
            };

            $scope.isAccountTypeFiltered = function (accountType) {
                return zemFilterService.isAccountTypeFiltered(accountType.id);
            };

            $scope.addFilteredAccountType = function (accountType) {
                if (!accountType || accountType === '') {
                    return;
                }

                zemFilterService.addFilteredAccountType(accountType);
                $scope.accountTypeToFilter = '';
            };

            $scope.removeFilteredAccountType = function (accountTypeId) {
                zemFilterService.removeFilteredAccountType(accountTypeId);
            };

            $rootScope.$on('$stateChangeSuccess', 
                function (event, toState, toParams, fromState, fromParams) {
                    updateVisibility();
            });

            function updateVisibility () {
                var isAllAccounts = $state.current.name.startsWith('main.allAccounts');
                $scope.agencyFilterVisible = isAllAccounts;
                $scope.accountTypeFilterVisible = isAllAccounts;
            }

            $scope.$watch('showArchivedSelected', function (newValue, oldValue) {
                if (newValue !== oldValue) {
                    zemFilterService.setShowArchived(newValue);
                }
            });

            $scope.$watch('showPublisherSelected', function (newValue, oldValue) {
                if (newValue !== oldValue) {
                    zemFilterService.setBlacklistedPublishers(newValue);
                }
            });

            $scope.$watch(zemFilterService.getShowArchived, function (newValue, oldValue) {
                if (newValue === oldValue) {
                    return;
                }
                $scope.refreshAvailableSources();
            });

            $scope.$watch(zemFilterService.getFilteredAgencies, function (newValue, oldValue) {
                if (newValue === oldValue) {
                    return;
                }
                $scope.refreshAgencies();
            }, true);

            $scope.$watch(zemFilterService.getFilteredAccountTypes, function (newValue, oldValue) {
                if (newValue === oldValue) {
                    return;
                }
                $scope.refreshAccountTypes();
            }, true);

            $scope.$watch(zemFilterService.getBlacklistedPublishers, function (newValue, oldValue) {
                if (newValue === oldValue) {
                    return;
                }

                $scope.showPublisherSelected = zemFilterService.getBlacklistedPublishers();
            });

            $scope.$on('$locationChangeStart', function () {
                // ui-bootstrap registers a listener on $locationChangeSuccess event
                // which closes the dropdown when the event triggers.
                // We don't want the dropdown to close upon changing the query string
                // parameters, so we remove all listeners on this event.
                // This can be done here because dropdown registers the listener on
                // the scope of the controller/directive that initialized it rather
                // than on it's isolated scope.
                $scope.$$listeners.$locationChangeSuccess = [];
            });

            $scope.$on('$stateChangeSuccess', function () {
                // Upon state change we do want to close the dropdown.
                $scope.isFilterOpen = false;
            });

            $scope.init = function () {
                $scope.showArchivedSelected = zemFilterService.getShowArchived();

                $scope.enablePublisherFilter = zemFilterService.getShowBlacklistedPublishers();
                $scope.showPublisherSelected = zemFilterService.getBlacklistedPublishers();
                $scope.refreshAvailableSources();
                $scope.refreshAgencies();
                $scope.refreshAccountTypes();
                updateVisibility();
            };

            $scope.init();
        }]
    };
}]);
