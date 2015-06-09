"use strict";

oneApp.directive('zemSelectionMenu', function () {
    return {
        restrict: 'E',
        scope: {
            customSelectionOptions: '=',
            selectAllCallback: '='
        },
        templateUrl: '/partials/zem_selection_menu.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
            $scope.toggleDropdown = function (ev) {
                if (ev.target.id === 'zem-all-checkbox') {
                    // prevent events from leaving the checkbox and suppressing checkbox switch
                    // very important switch - breaks the entire control if commented
                    ev.stopPropagation();
                    $scope.selectAllCallback($scope.selectedAll);
                }
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
