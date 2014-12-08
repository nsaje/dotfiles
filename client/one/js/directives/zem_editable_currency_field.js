/*globals oneApp*/
'use strict';

oneApp.directive('zemEditableCurrencyField', function() {
    return {
        restrict: 'E',
        scope: {
            onSave: '=',
            value: '=',
            rowId: '=',
            fractionSize: '=',
            replaceTrailingZeros: '=?'
        },
        templateUrl: '/partials/zem_editable_currency_field.html',
        controller: ['$scope', '$element', '$attrs', '$timeout', '$document', function ($scope, $element, $attrs, $timeout, $document) {
            $scope.editFormActive = false;
            $scope.errors = null;

            $scope.onError = function (errors) {
                $scope.errors = errors;
            };

            $scope.showEditForm = function () {
                $scope.formValue = $scope.value;
                $scope.editFormActive = true;

                $timeout(function () {
                    $element.find('.currency-input')[0].focus();
                    $document.bind('click', closeFormClickHandler);
                });
            };

            $scope.close = function () {
                $scope.editFormActive = false;
                $scope.errors = null;
                $document.unbind('click', closeFormClickHandler);
            };

            $scope.save = function (rowId) {
                $scope.value = $scope.formValue;
                $scope.onSave(rowId, $scope.formValue, $scope.close, $scope.onError)
            }

            function closeFormClickHandler(event) {
                var isClickedElementChildOfPopup = $element
                    .find('.edit-form')
                    .find(event.target)
                    .length > 0;

                if (isClickedElementChildOfPopup) {
                    return;
                }

                $timeout(function () {
                    $scope.close();
                });
            }
        }]
    };
});
