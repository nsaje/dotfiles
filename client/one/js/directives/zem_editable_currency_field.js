/*globals oneApp*/
'use strict';

oneApp.directive('zemEditableCurrencyField', function () {
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
            var inputElement = $element.find('.currency-input');

            $scope.editFormActive = false;
            $scope.errors = null;

            $scope.onError = function (errors) {
                $scope.errors = errors;
            };

            $scope.showEditForm = function () {
                $scope.formValue = $scope.value;
                $scope.editFormActive = true;

                $timeout(function () {
                    inputElement.focus();
                    $document.bind('click', closeFormClickHandler);
                    $document.bind('keyup', keyupHandler);
                });
            };

            inputElement.on('touchend', function (e) {
                // This prevents the form to be autoclosed
                // on focus in iOS Safari
                e.preventDefault();
            });

            $scope.close = function () {
                $scope.editFormActive = false;
                $scope.errors = null;

                $timeout(function () {
                    $document.unbind('click', closeFormClickHandler);
                    $document.unbind('keyup', keyupHandler);
                });
            };

            $scope.save = function () {
                $scope.onSave(
                    $scope.rowId,
                    $scope.formValue,
                    function () {
                        $scope.value = $scope.formValue;
                        $scope.close();
                    },
                    $scope.onError
                );
            };

            function keyupHandler (e) {
                if (e.keyCode === 27) {
                    // escape
                    $scope.close();
                } else if (e.keyCode === 13) {
                    // enter
                    $scope.save();
                }
            }

            function closeFormClickHandler (event) {
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
