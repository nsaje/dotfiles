angular.module('one.common').component('zemFileInput', {
    template:
        '<ng-transclude></ng-transclude>' +
        '<input tabindex="-1" type="file" ' +
        'style="width: 0; height: 0; overflow: hidden; position: absolute; padding: 0; margin: 0; opacity: 0" ' +
        '/>',
    bindings: {
        callback: '&zemFileInputChange',
        accept: '@zemFileInputAccept',
    },
    transclude: true,
    controller: function($element) {
        var $ctrl = this;
        $ctrl.$postLink = function() {
            var inputElement = $element.find('input[type=file]'),
                buttonElement = $element.find('[zem-file-input-trigger]');
            if ($ctrl.accept) inputElement.attr('accept', $ctrl.accept);
            buttonElement.click(function() {
                inputElement.click();
            });
            inputElement.bind('change', function() {
                if (inputElement[0].files[0] === undefined) return; // happens when user presses cancel
                $ctrl.callback({file: inputElement[0].files[0]});
                inputElement[0].value = ''; // we need to clear the value, otherwise the change handler will not be triggered if the same file is uploaded again
            });
        };
    },
});
