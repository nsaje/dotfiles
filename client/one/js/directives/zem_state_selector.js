/*globals constants*/
"use strict";

oneApp.directive('zemStateSelector', function () {
    return {
        restrict: 'E',
        scope: {
            id: '=',
            onChange: '=',
            isEditable: '=',
            value: '=',
            enabledValue: '=',
            pausedValue: '=',
            disabledMessage: '=',
            archived: '='
        },
        templateUrl: '/partials/zem_state_selector.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
            $scope.active = false;

            $scope.setState = function (state) {
                $scope.isOpen = false;

                if (state === $scope.value) {
                    return;
                }

                $scope.value = state;

                $scope.onChange($scope.id, state);
            };

            $scope.$watch('value', function(value) {
                $scope.active = $scope.value === $scope.enabledValue;
            });
        }]
    };
});
