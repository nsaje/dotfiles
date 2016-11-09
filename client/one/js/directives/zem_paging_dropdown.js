/* globals angular */
'use strict';

angular.module('one.legacy').directive('zemPagingDropdown', function () {
    return {
        restrict: 'E',
        scope: {
            page: '=',
        },
        templateUrl: '/partials/zem_paging_dropdown.html',
        controller: function ($scope, $element, $attrs) {
            $scope.selectAllCount = 4294967295;
            $scope.$watch('page.size', function (newValue, oldValue) {
                if (newValue === $scope.selectAllCount) {
                    $scope.selectionText = 'Show All';
                } else {
                    $scope.selectionText = newValue;
                }
            });

            $scope.select = function (value, text) {
                $scope.page.size = value;
                $scope.selectionText = text;
            };
        }
    };
});
