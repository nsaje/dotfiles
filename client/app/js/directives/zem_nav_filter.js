/*globals $,oneApp,constants,options*/
"use strict";

oneApp.directive('zemNavFilter', ['config', '$state', function(config, $state) {
    return {
        restrict: 'E',
        templateUrl: config.static_url + '/partials/zem_nav_filter.html',
        scope: {
            account: '=zemCurrentAccount',
            accountsData: '=zemAllAccounts',
            canAccessAccounts: '@zemCanAccessAccounts',
            canAccessCampaigns: '@zemCanAccessCampaigns',
            defaultAccountState: '@zemDefaultAccountState',
            defaultCampaignState: '@zemDefaultCampaignState',
            defaultAdGroupState: '@zemDefaultAdGroupState',
        },
        controller: ['$scope', '$element', '$attrs', '$http', 'api', function ($scope, $element, $attrs, $http, api) {
            $scope.accounts = null;
            $scope.campaigns = null;
            $scope.adGroups = null;
            $scope.navSelector = null;

            $scope.navSelectorOptions = {
                allowClear: false,
                minimumInputLength: 1,
                placeholder: 'search',
                containerCssClass: 'nav-search',
                dropdownCssClass: 'nav-search',
                formatInputTooShort: function (input, min) {
                    return 'type to start searching';
                },
                formatSelection: function (item) {
                    return item.text;
                },
                formatResult: function (item) {
                    return item.text;
                }
            };
g
            $scope.$watch('accountsData', function (newValue) {
                if (!$scope.accountsData || !$scope.accountsData.length) {
                    return;
                }

                $scope.accounts = [];
                $scope.campaigns = [];
                $scope.adGroups = [];

                $scope.accountsData.forEach(function (account, i) {
                    $scope.accounts.push({id: constants.entityType.account + ':' + account.id, name: account.name});
                    account.campaigns.forEach(function (campaign, j) {
                        $scope.campaigns.push({id: constants.entityType.campaign + ':' + campaign.id, name: campaign.name});
                        campaign.adGroups.forEach(function (adGroup, k) {
                            $scope.adGroups.push({id: constants.entityType.adGroup + ':' + adGroup.id, name: adGroup.name});
                        });
                    });
                });
            });

            $scope.$watch('account', function (newValue) {
                $scope.navSelector = $scope.account && constants.entityType.account + ':' + $scope.account.id || null;
            });

            $scope.navSelectorChanged = function () {
                if (!$scope.navSelector) {
                    return;
                }

                var state = null,
                    id = $scope.navSelector.split(':');

                if (id[0] === constants.entityType.account) {
                    state = $scope.defaultAccountState;
                } else if (id[0] === constants.entityType.campaign) {
                    state = $scope.defaultCampaignState;
                } else if (id[0] === constants.entityType.adGroup) {
                    state = $scope.defaultAdGroupState;
                }

                if (state) {
                    $state.go(state, {id: id[1]});
                }

                $scope.navSelector = $scope.account && constants.entityType.account + ':' + $scope.account.id || null;
            };
        }]
    };
}]);
