/*globals constants*/
"use strict";

oneApp.directive('zemStateSelector', function () {
    return {
        restrict: 'E',
        scope: {
            id: '=',
            onChange: '=',
            isEditable: '=',
            value: '='
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

            setActive();
        }]
    }
});
