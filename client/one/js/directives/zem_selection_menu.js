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
            $scope.selectAll = function(ev) {
                $scope.selectAllCallback($scope.selectedAll);
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
