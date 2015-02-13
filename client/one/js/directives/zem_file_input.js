/* globals oneApp */
'use strict';

oneApp.directive('zemFileInput', ['$parse', function($parse) {
    function createInputElement() {
        return angular.element('<input type="file">').css({
            width: 0,
            height: 0,
            overflow: 'hidden',
            position: 'absolute',
            padding: 0,
            margin: 0,
            opacity: 0
        }).attr('accept', '.csv');
    }

    return {
        restrict: 'A',
        link: function(scope, element, attrs) {
            var model = $parse(attrs.zemFileInput);
            var inputElement = createInputElement();

            element.after(inputElement);

            inputElement.bind('change', function() {
                scope.$apply(function() {
                    model.assign(scope, inputElement[0].files[0]);
                });
            });

            element.bind('click', function() {
                inputElement.click();
            });
        }
    };
}]);
