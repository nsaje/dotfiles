/*globals oneApp*/
'use strict';

oneApp.directive('zemEditableCurrencyField', function() {
    return {
        restrict: 'E',
        scope: {
            onSave: '=',
            value: '=',
            rowId: '=',
            fractionSize: '='
        },
        templateUrl: '/partials/zem_editable_currency_field.html',
        controller: ['$scope', '$element', '$attrs', '$timeout', '$document', function ($scope, $element, $attrs, $timeout, $document) {
            $scope.originalValue = $scope.value;
            $scope.editFormActive = false;
            $scope.errors = null;

            $scope.onError = function (errors) {
                $scope.errors = errors;
            };

            $scope.showEditForm = function () {
                $scope.editFormActive = true;

                $timeout(function () {
                    $element.find('.currency-input')[0].focus();
                });
            };

            $scope.cancel = function () {
                $scope.editFormActive = false;
                $scope.errors = null;
                $scope.value = $scope.originalValue;
            };

            $document.bind('click', function(event){
                var isClickedElementChildOfPopup = $element
                    .find(event.target)
                    .length > 0;

                if (isClickedElementChildOfPopup) {
                    return;
                }

                $timeout(function () {
                    $scope.cancel();
                });
            });
        }]
    };
});
