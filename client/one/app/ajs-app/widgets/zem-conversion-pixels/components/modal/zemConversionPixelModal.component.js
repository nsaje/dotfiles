angular.module('one.widgets').component('zemConversionPixelModal', {
    bindings: {
        resolve: '<',
        close: '&',
    },
    template: require('./zemConversionPixelModal.component.html'),
    controller: function ($rootScope, zemPermissions) {
        var $ctrl = this;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.submit = submit;
        $ctrl.cancel = cancel;
        $ctrl.clearError = clearError;
        $ctrl.getRequest = getRequest;

        $ctrl.$onInit = function () {
            $ctrl.isCreationMode = !$ctrl.resolve.pixel;

            $ctrl.title = $ctrl.isCreationMode ? 'Add a New Pixel' : 'Edit Pixel';
            $ctrl.buttonText = $ctrl.isCreationMode ? 'Add Pixel' : 'Save Pixel';

            $ctrl.stateService = $ctrl.resolve.stateService;
            $ctrl.state = $ctrl.stateService.getState();
            $ctrl.pixel = $ctrl.isCreationMode ? {name: '', audienceEnabled: false} : $ctrl.resolve.pixel;
            $ctrl.audiencePixel = $ctrl.stateService.getState().conversionPixels
                .filter(function (pixie) { return pixie.audienceEnabled; })[0];
        };

        function getRequest () {
            return $ctrl.isCreationMode ? $ctrl.state.requests.create : $ctrl.state.requests.update[$ctrl.pixel.id];
        }

        function submit () {
            var fn = $ctrl.isCreationMode ? $ctrl.stateService.create : $ctrl.stateService.update;

            fn($ctrl.pixel).then(function () {
                // FIXME: avoid broadcast in pixelAudienceEnabled propagation
                if ($ctrl.pixel.audienceEnabled) {
                    $rootScope.$broadcast('pixelAudienceEnabled', {pixel: $ctrl.pixel});
                }

                $ctrl.close();
            });
        }

        function cancel () {
            $ctrl.close();
        }

        function clearError () {
            $ctrl.stateService.clearRequestError(getRequest());
        }
    }
});
