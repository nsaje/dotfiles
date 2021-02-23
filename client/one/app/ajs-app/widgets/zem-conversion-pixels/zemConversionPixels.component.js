require('./zemConversionPixels.component.less');

angular.module('one.widgets').component('zemConversionPixels', {
    bindings: {
        account: '<',
        onAudiencePixelUpdate: '&',
    },
    template: require('./zemConversionPixels.component.html'),
    controller: function(
        $scope,
        $uibModal,
        zemAuthStore,
        zemConversionPixelsStateService
    ) {
        var $ctrl = this;
        $ctrl.hasPermission = zemAuthStore.hasPermission.bind(zemAuthStore);
        $ctrl.isPermissionInternal = zemAuthStore.isPermissionInternal.bind(
            zemAuthStore
        );

        $ctrl.$onInit = function() {
            $ctrl.stateService = zemConversionPixelsStateService.getInstance(
                $ctrl.account
            );
            $ctrl.stateService.initialize();
            $ctrl.state = $ctrl.stateService.getState();

            $ctrl.orderField = 'name';
            $ctrl.orderReverse = false;

            $ctrl.archiveConversionPixel = $ctrl.stateService.archive;
            $ctrl.restoreConversionPixel = $ctrl.stateService.restore;
        };

        $ctrl.$onDestroy = function() {
            $ctrl.stateService.destroy();
        };

        $ctrl.addConversionPixel = function() {
            $uibModal.open({
                component: 'zemConversionPixelModal',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    stateService: $ctrl.stateService,
                    pixel: null, // Creation mode
                },
            });
        };

        $ctrl.editConversionPixel = function(pixel) {
            $uibModal.open({
                component: 'zemConversionPixelModal',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    stateService: $ctrl.stateService,
                    pixel: angular.copy(pixel),
                },
            });
        };

        $ctrl.copyConversionPixelTag = function(conversionPixel) {
            $uibModal.open({
                component: 'zemCopyConversionPixelTag',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    conversionPixelTag: function() {
                        return $ctrl.getConversionPixelTag(
                            conversionPixel.name,
                            conversionPixel.url
                        );
                    },
                },
            });
        };

        $ctrl.getConversionPixelTag = function(name, url) {
            return (
                '<!-- ' +
                name +
                '-->\n<img src="' +
                url +
                '" referrerpolicy="no-referrer-when-downgrade" height="1" width="1" border="0" alt="" />'
            );
        };
    },
});
