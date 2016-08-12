/* globals oneApp */
'use strict';

oneApp.directive('zemPagingDropdown', function () {
    return {
        restrict: 'E',
        scope: {
            selection: '=',
            selectionText: '=',
            selectAllCount: '='
        },
        templateUrl: '/partials/zem_paging_dropdown.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
            $scope.selectAllCount = 4294967295;
            $scope.$watch('selection.size', function (newValue, oldValue) {
                if (newValue === $scope.selectAllCount) {
                    $scope.selectionText = 'Show All';
                } else {
                    $scope.selectionText = newValue;
                }
            });

            $scope.select = function (value, text) {
                $scope.selection.size = value;
                $scope.selectionText = text;
            };
        }]
    };
});
