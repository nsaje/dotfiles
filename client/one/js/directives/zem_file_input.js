/* globals oneApp, angular */
'use strict';

oneApp.directive('zemFileInput', ['$parse', function ($parse) {
    function createInputElement () {
        return angular.element('<input type="file">').css({
            width: 0,
            height: 0,
            overflow: 'hidden',
            position: 'absolute',
            padding: 0,
            margin: 0,
            opacity: 0,
        }).attr('accept', '.csv');
    }

    function bindInputElement (inputElement, scope, varName) {
        var model = $parse(varName);

        inputElement.unbind('change');
        inputElement.bind('change', function () {
            scope.$apply(function () {
                model.assign(scope, inputElement[0].files[0]);
            });
        });
    }

    return {
        restrict: 'A',
        link: function (scope, element, attrs) {
            var inputElement = createInputElement();

            element.after(inputElement);
            bindInputElement(inputElement, scope, attrs.zemFileInput);

            element.bind('click', function () {
                inputElement.click();
            });

            scope.$watch(attrs.zemFileInput, function () {
                bindInputElement(inputElement, scope, attrs.zemFileInput);
            });
        },
    };
}]);
