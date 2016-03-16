/* globals oneApp */
'use strict';

oneApp.directive('zemRetargeting', ['config', 'zemFilterService', '$state', function (config, zemFilterService, $state) { // eslint-disable-line max-len
    return {
        restrict: 'E',
        scope: {
            selectedAdgroupIds: '=zemSelectedAdgroupIds',
            account: '=zemAccount',
            retargetableAdgroups: '=zemRetargetableAdgroups',
        },
        templateUrl: '/partials/zem_retargeting.html',
        controller: ['$scope', function ($scope) {
            $scope.config = config;
            $scope.selected = {adgroup: undefined};

            $scope.selectedAdgroups = function () {
                var result = [];
                $scope.retargetableAdgroups.forEach(function (adgroup) {
                    if ($scope.selectedAdgroupIds.indexOf(adgroup.id) >= 0) {
                        result.push(adgroup);
                    }
                });
                return result;
            };

            $scope.availableAdgroups = function () {
                if (!$scope.retargetableAdgroups) {
                    return [];
                }

                var adgroups = $scope.retargetableAdgroups.filter(function (adgroup) {
                    return $scope.selectedAdgroupIds.indexOf(adgroup.id) < 0;
                }).filter(function (adgroup) {
                    return adgroup.id !== parseInt($state.params.id);
                });

                adgroups.forEach(function (adgroup) {
                    adgroup.suffix = '';
                    if (adgroup.archived) {
                        adgroup.suffix = ' (Archived)';
                    }
                });

                return adgroups;
            };

            $scope.groupByCampaign = function (adgroup) {
                return adgroup.campaignName;
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
