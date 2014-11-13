/*globals oneApp*/
'use strict';

oneApp.directive('zemEditableCurrencyField', function() {
    return {
        restrict: 'E',
        scope: {
            onSave: '=',
            value: '@',
            rowId: '@',
            fractionSize: '@'
        },
        templateUrl: '/partials/zem_editable_currency_field.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
            $scope.originalValue = $scope.value;
            $scope.editFormActive = false;
            $scope.errors = null;

            $scope.onError = function (errors) {
                $scope.errors = errors;
            };

            $scope.cancel = function () {
                $scope.editFormActive = false;
                $scope.errors = null;
                $scope.value = $scope.originalValue;
            };
        }]
    };
});
