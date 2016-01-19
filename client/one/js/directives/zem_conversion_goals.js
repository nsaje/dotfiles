/*global $,oneApp,constants*/
"use strict";

oneApp.directive('zemConversionGoals', ['config', '$window', function(config, $window) {

    return {
        restrict: 'E',
        scope: {
            hasPermission: '=zemHasPermission',
            isPermissionInternal: '=zemIsPermissionInternal',
            campaign: '=zemCampaign',
            account: '=zemAccount'
        },
        templateUrl: '/partials/zem_conversion_goals.html',
        controller: ['$scope', '$modal', 'api', function ($scope, $modal, api) {
            $scope.requestInProgress = false;
            $scope.error = false;
            $scope.conversionGoals = [];
            $scope.removeInProgress = false;

            function constructConversionGoalRow (row) {
                var ret = {
                    id: row.id,
                    rows: [
                        {title: 'Name', value: row.name},
                        {title: 'Type', value: constants.conversionGoalTypeText[row.type]}
                    ]
                };

                if (row.type === constants.conversionGoalType.PIXEL) {
                    ret.rows.push(
                        {title: 'Conversion window', value: constants.conversionWindowText[row.conversionWindow]},
                        {
                            title: 'Pixel URL',
                            value: row.pixel.url,
                            link: {
                                text: 'COPY TAG',
                                click: function () {
                                    var scope = $scope.$new(true);
                                    scope.conversionPixelTag = $scope.getConversionPixelTag(row.pixel.url);

                                    var modalInstance = $modal.open({
                                        templateUrl: '/partials/copy_conversion_pixel_modal.html',
                                        windowClass: 'modal',
                                        scope: scope
                                    });

                                    return modalInstance;
                                }
                            }
                        }
                    );
                } else if (row.type === constants.conversionGoalType.GA) {
                    ret.rows.push(
                        {title: 'Goal name', value: row.goalId}
                    );
                } else if (row.type === constants.conversionGoalType.OMNITURE) {
                    ret.rows.push(
                        {title: 'Event name', value: row.goalId}
                    );
                }

                return ret;
            };

            $scope.getConversionGoals = function () {
                $scope.requestInProgress = true;
                api.conversionGoal.list($scope.campaign.id).then(
                    function (data) {
                        $scope.conversionGoals = data.rows.map(constructConversionGoalRow);
                        $scope.availablePixels = data.availablePixels;
                        $scope.error = false;
                    },
                    function () {
                        $scope.error = true;
                    }
                ).finally(function () {
                    $scope.requestInProgress = false;
                });
            };

            $scope.addConversionGoal = function () {
                var modalInstance = $modal.open({
                    templateUrl: '/partials/add_conversion_goal_modal.html',
                    controller: 'AddConversionGoalModalCtrl',
                    windowClass: 'modal',
                    scope: $scope
                });

                modalInstance.result.then(function() {
                    $scope.getConversionGoals();
                });

                return modalInstance;
            };

            $scope.removeConversionGoal = function (id) {
                $scope.removeInProgress = true;
                api.conversionGoal.delete($scope.campaign.id, id).then(
                    function () {
                        $scope.conversionGoals = $scope.conversionGoals.filter(function (conversionGoalRow) {
                            if (conversionGoalRow.id === id) {
                                return false;
                            }

                            return true;
                        });
                        $scope.error = false;
                    },
                    function () {
                        $scope.error = true;
                    }
                ).finally(function() {
                    $scope.removeInProgress = false;
                });
            };

            $scope.getConversionPixelTag = function (url) {
                return '<img src="' + url + '" height="1" width="1" border="0" alt="" />';
            };

            $scope.getConversionGoals();
        }]
    };
}]);
