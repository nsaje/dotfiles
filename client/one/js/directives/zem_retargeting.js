/* globals oneApp */
'use strict';

oneApp.directive('zemRetargeting', ['config', 'zemFilterService', function (config, zemFilterService) {
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

            $scope.selectedAdgroups = function () {
                return $scope.selectedAdgroupIds.map(function (id) {
                    return $scope.getAdgroupById(id);
                });
            };

            $scope.getAdgroupById = function (id) {
                var result;

                $scope.account.campaigns.forEach(function (campaign) {
                    campaign.adGroups.forEach(function (adgroup) {
                        if (adgroup.id === id) {
                            result = adgroup;
                        }
                    });
                });

                return result;
            };

            $scope.availableAdgroups = function () {
                return $scope.account.campaigns.reduce(function (result, campaign) {
                    var adgroups = campaign.adGroups.filter(function (adgroup) {
                        return !adgroup.archived || zemFilterService.isArchivedFilterOn();
                    }).filter(function (adgroup) {
                        return $scope.selectedAdgroupIds.indexOf(adgroup.id) < 0;
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
