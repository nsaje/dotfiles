/* global oneApp */
'use strict';

oneApp.directive('zemHistory', [function () {
    return {
        restrict: 'E',
        templateUrl: '/partials/zem_history.html',
        scope: {
            params: '=zemParams',
        },
        controller: ['$scope', 'api', function ($scope, api) {
            $scope.alerts = [];
            $scope.history = [];
            $scope.requestInProgress = false;
            $scope.order = 'datetime';
            $scope.orderAsc = false;

            $scope.changeOrder = function (field) {
                $scope.order = field;
                $scope.orderAsc = !$scope.orderAsc;
                $scope.getHistory();
            };

            $scope.getOrderClass = function (field) {
                if ($scope.order !== field) {
                    return '';
                }

                if ($scope.orderAsc) {
                    return 'ordered-reverse';
                }
                return 'ordered';
            };

            $scope.getHistory = function () {
                var order = (!$scope.orderAsc && '-' || '') + $scope.order;
                $scope.requestInProgress = true;
                api.history.get($scope.params, order).then(
                    function (data) {
                        $scope.history = data.history;
                    }
                ).finally(function () {
                    $scope.requestInProgress = false;
                });
            };

            $scope.$watch('params', function () {
                $scope.getHistory();
            });
        }],
    };
}]);
