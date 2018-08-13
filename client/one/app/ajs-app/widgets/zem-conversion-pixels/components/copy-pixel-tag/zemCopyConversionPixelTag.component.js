angular.module('one.widgets').component('zemCopyConversionPixelTag', {
    bindings: {
        resolve: '<',
        close: '&',
    },
    template: require('./zemCopyConversionPixelTag.component.html'), // eslint-disable-line max-len
    controller: function() {
        var $ctrl = this;
        $ctrl.$onInit = function() {
            $ctrl.conversionPixelTag = $ctrl.resolve.conversionPixelTag;
        };
    },
});
