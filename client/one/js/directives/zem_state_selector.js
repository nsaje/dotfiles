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
            maintenance: '='
        },
        templateUrl: '/partials/zem_state_selector.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
            $scope.constants = constants;
            $scope.active = false;

            var setActive = function () {
                $scope.active = $scope.value === constants.adGroupSettingsState.ACTIVE;
            };

            $scope.setState = function (state) {
                $scope.isOpen = false;

                if (state === $scope.value) {
                    return;
                }

                $scope.value = state;
                setActive();

                $scope.onChange($scope.id, state);
            };

            $scope.getDisabledMessage = function (row) {
                return $scope.maintenance ? 
                    'This source is currently in maintenance mode.' : 
                    'This source must be managed manually.';
            };

            setActive();
        }]
    }
});
