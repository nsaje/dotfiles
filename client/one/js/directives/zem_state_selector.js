/*globals constants*/
"use strict";

oneApp.directive('zemStateSelector', function () {
    return {
        restrict: 'E',
        scope: {
            id: '=',
            onChange: '=',
            onAutopilotChange: '=',
            isEditable: '=',
            value: '=',
            enabledValue: '=',
            pausedValue: '=',
            disabledMessage: '=',
            archived: '=',
            autopilotEnabledValue: '=',
            autopilotPausedValue: '=',
            autopilotValue: '=',
            autopilotInternal: '=',
            autopilotShown: '='
        },
        templateUrl: '/partials/zem_state_selector.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
            $scope.active = false;

            $scope.setState = function (state, autopilotState) {
                $scope.isOpen = false;

                if ( !$scope.active && autopilotState === $scope.autopilotEnabledValue) {
                    return;
                }
                if (state === $scope.value && autopilotState === $scope.autopilotValue) {
                    return;
                }

                var newState = ( (state === $scope.value) ? undefined : state );
                $scope.value = state;

                var newAutopilotState = ( (autopilotState === $scope.autopilotValue) ? undefined : autopilotState );
                $scope.autopilotValue = autopilotState;

                $scope.onChange($scope.id, newState, newAutopilotState);
            };
            $scope.$watch('value', function(value) {
                $scope.active = $scope.value === $scope.enabledValue;
            });
            $scope.$watch('autopilotValue', function(autopilotValue) {
                if ($scope.autopilotEnabledValue === undefined) {
                    // autopilot is optional, so if values are not set, do nothing
                    return;
                }
                $scope.autopilotActive = $scope.autopilotValue === $scope.autopilotEnabledValue;
            });
        }]
    };
});
