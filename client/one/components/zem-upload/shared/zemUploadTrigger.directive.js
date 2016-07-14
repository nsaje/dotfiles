/* globals oneApp */
'use strict';

oneApp.directive('zemUploadTrigger', ['$modal', '$rootScope', 'zemUploadEndpointService', function ($modal, $rootScope, zemUploadEndpointService) { // eslint-disable-line max-len
    return {
        restrict: 'A',
        replace: true,
        scope: {},
        bindToController: {
            adGroup: '=zemUploadAdGroup',
            onSave: '=zemUploadOnSave',
        },
        controllerAs: 'ctrl',
        link: function (scope, element, attrs, ctrl) {
            element.on('click', function () {
                var modalScope = $rootScope.$new();
                modalScope.api = zemUploadEndpointService.createEndpoint(ctrl.adGroup.id);
                modalScope.adGroup = ctrl.adGroup;
                modalScope.onSave = ctrl.onSave;

                $modal.open({
                    templateUrl: '/components/zem-upload/templates/zem_upload.html',
                    ctrl: 'zemUploadModalCtrl',
                    windowClass: 'modal-zem-upload',
                    scope: modalScope,
                });
            });
        },
        controller: [function () {}],
    };
}]);
