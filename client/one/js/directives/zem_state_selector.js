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

            $scope.setState = function (state) {
                $scope.isOpen = false;

                if (state === $scope.value && !$scope.autopilotActive) {
                    return;
                }

                $scope.value = state;

                if ($scope.autopilotActive) {
                    $scope.autopilotValue = $scope.autopilotPausedValue
                    $scope.onAutopilotChange($scope.id, $scope.autopilotPausedValue)
                }

                $scope.onChange($scope.id, state);
            };
            $scope.setAutopilotState = function (autopilotState) {
              $scope.isOpen = false;

              if (autopilotState === $scope.autopilotEnabledValue) {
                  if ($scope.value !== $scope.enabledValue) {
                    return;
                  }
                  if (autopilotState === $scope.autopilotValue){
                    return;
                  }
              }

              $scope.autopilotValue = autopilotState

              $scope.onAutopilotChange($scope.id, autopilotState)

            };
            $scope.$watch('value', function(value) {
                $scope.active = $scope.value === $scope.enabledValue;
            });
            $scope.$watch('autopilotValue', function(autopilotValue) {
                $scope.autopilotActive = (
                  $scope.autopilotValue === $scope.autopilotEnabledValue
                  && $scope.autopilotValue !== undefined
                  && $scope.autopilotEnabledValue !== undefined
                );
            });
        }]
    };
});
