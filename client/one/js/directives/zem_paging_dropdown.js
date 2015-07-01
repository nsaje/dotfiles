"use strict";

oneApp.directive('zemPagingDropdown', function () {
    return {
        restrict: 'E',
        scope: {
            counts: '=',
            selection: '=',
            selectionText: '=',
        },
        templateUrl: '/partials/zem_paging_dropdown.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
            $scope.$watch('selection', function(newValue, oldValue) {
                if (newValue === 4294967295) {
                    $scope.selectionText = 'Select All';
                } else {
                    $scope.selectionText = newValue;
                }
            });

            $scope.select = function (value, text) {
                $scope.selection = value;
                $scope.selectionText = text;
            };
        }]
    };
});
