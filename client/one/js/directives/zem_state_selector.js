/*globals constants*/
'use strict';

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
            archived: '=',
            enablingAutopilotSourcesNotAllowed: '='
        },
        templateUrl: '/partials/zem_state_selector.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
            $scope.active = false;

            $scope.setState = function (state) {
                $scope.isOpen = false;
                // prevent enabling source when enabling not allowed by the autopilot
                if (!$scope.active && $scope.enablingAutopilotSourcesNotAllowed) {
                    return;
                }

                // do nothing when no change
                if (state === $scope.value) {
                    return;
                }

                var newState = ( (state === $scope.value) ? undefined : state );
                $scope.value = state;

                $scope.onChange($scope.id, newState);
            };
            $scope.$watch('value', function (value) {
                $scope.active = $scope.value === $scope.enabledValue;
            });
        }]
    };
});
