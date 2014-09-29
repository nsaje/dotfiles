/*globals $,oneApp,constants,options*/
"use strict";

oneApp.directive('zemNavSearch', ['config', '$state', function(config, $state) {
    return {
        restrict: 'E',
        templateUrl: '/partials/zem_nav_search.html',
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
                placeholder: 'Search',
                containerCssClass: 'select2-nav-search',
                dropdownCssClass: 'select2-nav-search',
                formatInputTooShort: 'type to start searching',
                formatNoMatches: 'no matches found',
                formatSelection: function (item) {
                    return item.text;
                },
                formatResult: function (item) {
                    return item.text;
                }
            };

            $scope.$watch('accountsData', function (newValue) {
                if (!$scope.accountsData || !$scope.accountsData.length) {
                    return;
                }

                $scope.accounts = [];
                $scope.campaigns = [];
                $scope.adGroups = [];

                $scope.accountsData.forEach(function (account, i) {
                    $scope.accounts.push({id: constants.entityType.ACCOUNT + ':' + account.id, name: account.name});
                    account.campaigns.forEach(function (campaign, j) {
                        $scope.campaigns.push({id: constants.entityType.CAMPAIGN + ':' + campaign.id, name: campaign.name});
                        campaign.adGroups.forEach(function (adGroup, k) {
                            $scope.adGroups.push({id: constants.entityType.AD_GROUP + ':' + adGroup.id, name: adGroup.name});
                        });
                    });
                });
            });

            $scope.$watch('account', function (newValue) {
                $scope.navSelector = $scope.account && constants.entityType.ACCOUNT + ':' + $scope.account.id || null;
            });

            $scope.navSelectorChanged = function () {
                if (!$scope.navSelector) {
                    return;
                }

                var state = null,
                    id = $scope.navSelector.split(':');

                if (id[0] === constants.entityType.ACCOUNT) {
                    state = $scope.defaultAccountState;
                } else if (id[0] === constants.entityType.CAMPAIGN) {
                    state = $scope.defaultCampaignState;
                } else if (id[0] === constants.entityType.AD_GROUP) {
                    state = $scope.defaultAdGroupState;
                }

                if (state) {
                    $state.go(state, {id: id[1]});
                }

                $scope.navSelector = $scope.account && constants.entityType.ACCOUNT + ':' + $scope.account.id || null;
            };
        }]
    };
}]);
