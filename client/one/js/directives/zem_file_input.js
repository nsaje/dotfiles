/* globals angular */
'use strict';

angular.module('one.legacy').component('zemFileInput', {
    template: '<ng-transclude></ng-transclude><input type="file" style="width: 0; height: 0; overflow: hidden; position: absolute; padding: 0; margin: 0; opacity: 0" />',
    bindings: {
        callback: '&zemFileInputChange',
        accept: '@zemFileInputAccept',
    },
    transclude: true,
    controller: ['$element', function ($element) {
        var $ctrl = this;
        $ctrl.$postLink = function () {
            var inputElement = $element.find('input[type=file]'),
                buttonElement = $element.find('[zem-file-input-trigger]');
            if ($ctrl.accept) inputElement.attr('accept', $ctrl.accept);
            buttonElement.click(function () {
                inputElement.click();
            });
            inputElement.bind('change', function () {
                if (inputElement[0].files[0] === undefined) return; // happens when user presses cancel
                $ctrl.callback({file: inputElement[0].files[0]});
            });
        };
    }],
});
