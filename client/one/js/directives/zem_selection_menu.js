'use strict';

oneApp.directive('zemSelectionMenu', function () {
    return {
        restrict: 'E',
        scope: {
            config: '='
        },
        templateUrl: '/partials/zem_selection_menu.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
            var selectAllCheckbox = $element.find('#zem-all-checkbox')[0];

            $scope.$watch('config.partialSelection', function (newVal, oldVal) {
                if (newVal === oldVal) {
                    return;
                }

                selectAllCheckbox.indeterminate = newVal;
            });

            $scope.selectAll = function (ev) {
                if ($scope.config.partialSelection) {
                    // if checkbox is in ideterminate state,
                    // clear selection upon click
                    $scope.selectedAll = false;
                }

                $scope.config.selectAllCallback($scope.selectedAll);
                ev.stopPropagation();
            };

            $scope.handleOptionClick = function (option) {
                $scope.selectedAll = false;
                option.callback();
            };

            $scope.handleOptionItemClick = function (option, item) {
                $scope.selectedAll = false;
                option.callback(item.id);
            };
        }]
    };
});
