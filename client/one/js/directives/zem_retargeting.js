/* globals oneApp, angular */
'use strict';

oneApp.directive('zemRetargeting', ['config', 'zemFilterService', '$state', 'zemNavigationService', function (config, zemFilterService, $state, zemNavigationService) { // eslint-disable-line max-len
    return {
        restrict: 'E',
        scope: {
            selectedAdgroupIds: '=zemSelectedAdgroupIds',
            account: '=zemAccount',
        },
        templateUrl: '/partials/zem_retargeting.html',
        controller: ['$scope', function ($scope) {
            $scope.config = config;
            $scope.selected = {adgroup: undefined};
            $scope.campaigns = angular.copy($scope.account.campaigns) || [];

            zemNavigationService.onUpdate($scope, function () {
                zemNavigationService.getAccount($scope.account.id).then(function (data) {
                    // make a copy of campaigns so we don't change original objects
                    $scope.campaigns = angular.copy(data.account.campaigns);
                });
            });

            $scope.selectedAdgroups = function () {
                var result = [];
                $scope.campaigns.forEach(function (campaign) {
                    campaign.adGroups.forEach(function (adgroup) {
                        if ($scope.selectedAdgroupIds.indexOf(adgroup.id) >= 0) {
                            result.push(adgroup);
                        }
                    });
                });

                return result;
            };

            $scope.availableAdgroups = function () {
                return $scope.campaigns.reduce(function (result, campaign) {
                    var adgroups = campaign.adGroups.filter(function (adgroup) {
                        return !adgroup.archived || zemFilterService.isArchivedFilterOn();
                    }).filter(function (adgroup) {
                        return $scope.selectedAdgroupIds.indexOf(adgroup.id) < 0;
                    }).filter(function (adgroup) {
                        return adgroup.id !== parseInt($state.params.id);
                    }).map(function (adgroup) {
                        // add campaign info to each item for grouping
                        adgroup.campaign = campaign;
                        return adgroup;
                    });

                    return result.concat(adgroups);
                }, []);
            };

            $scope.groupByCampaign = function (adgroup) {
                return adgroup.campaign.name;
            };

            $scope.removeSelectedAdgroup = function (adgroup) {
                var selectedIdx = $scope.selectedAdgroupIds.indexOf(adgroup.id);
                if (selectedIdx >= 0) {
                    $scope.selectedAdgroupIds.splice(selectedIdx, 1);
                }
            };

            $scope.addAdgroup = function (adgroup) {
                $scope.selectedAdgroupIds.push(adgroup.id);
                $scope.selected.adgroup = undefined;
            };
        }],
    };
}]);
