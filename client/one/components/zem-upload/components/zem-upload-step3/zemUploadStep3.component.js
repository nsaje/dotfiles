/* globals oneApp */
'use strict';

oneApp.directive('zemUploadStep3', [function () { // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        bindToController: {
            callback: '&',
            numSuccessful: '=',
            adGroup: '=',
            closeModal: '=close',
        },
        controllerAs: 'ctrl',
        templateUrl: '/components/zem-upload/components/zem-upload-step3/zemUploadStep3.component.html',
        controller: ['config', function (config) {
            var vm = this;
            vm.config = config;

            vm.close = function () {
                vm.closeModal();
            };
        }],
    };
}]);
