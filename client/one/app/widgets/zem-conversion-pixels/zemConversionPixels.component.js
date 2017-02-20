angular.module('one.widgets').component('zemConversionPixels', {
    bindings: {
        account: '<',
        onAudiencePixelUpdate: '&'
    },
    templateUrl: '/app/widgets/zem-conversion-pixels/zemConversionPixels.component.html',
    controller: function ($scope, api, $uibModal, zemPermissions, zemConversionPixelsStateService, zemDataFilterService) { // eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.$onInit = function () {
            $ctrl.stateService = zemConversionPixelsStateService.getInstance($ctrl.account);
            $ctrl.stateService.initialize();
            $ctrl.state = $ctrl.stateService.getState();

            $ctrl.orderField = 'name';
            $ctrl.orderReverse = false;

            $ctrl.archiveConversionPixel = $ctrl.stateService.archive;
            $ctrl.restoreConversionPixel = $ctrl.stateService.restore;
        };

        $ctrl.addConversionPixel = function () {
            $uibModal.open({
                component: 'zemConversionPixelModal',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    stateService: $ctrl.stateService,
                    pixel: null // Creation mode
                }
            });
        };

        $ctrl.editConversionPixel = function (pixel) {
            $uibModal.open({
                component: 'zemConversionPixelModal',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    stateService: $ctrl.stateService,
                    pixel: angular.copy(pixel),
                }
            });
        };

        $ctrl.copyConversionPixelTag = function (conversionPixel) {
            $uibModal.open({
                component: 'zemCopyConversionPixelTag',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    conversionPixelTag: function () {
                        return $ctrl.getConversionPixelTag(conversionPixel.name, conversionPixel.url);
                    }
                }
            });
        };

        $ctrl.filterConversionPixels = function (conversionPixel) {
            if (zemDataFilterService.getShowArchived()) {
                return true;
            }
            return !conversionPixel.archived;
        };

        $ctrl.getConversionPixelTag = function (name, url) {
            return '<!-- ' + name + '-->\n<img src="' + url + '" height="1" width="1" border="0" alt="" />';
        };

    }
});
