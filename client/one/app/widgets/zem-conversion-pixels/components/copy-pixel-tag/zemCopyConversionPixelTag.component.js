angular.module('one.widgets').component('zemCopyConversionPixelTag', {
    bindings: {
        resolve: '<',
        close: '&'
    },
    templateUrl: '/app/widgets/zem-conversion-pixels/components/copy-pixel-tag/zemCopyConversionPixelTag.component.html', // eslint-disable-line max-len
    controller: function () {
        var $ctrl = this;
        $ctrl.$onInit = function () {
            $ctrl.conversionPixelTag = $ctrl.resolve.conversionPixelTag;
        };
    }
});
