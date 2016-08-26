/* globals oneApp */
'use strict';

oneApp.directive('zemCustomAudiencesModalTrigger', ['$modal', '$rootScope', function ($modal, $rootScope) { // eslint-disable-line max-len
    return {
        restrict: 'A',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        link: function (scope, element, attrs, ctrl) {
            element.on('click', function () {
                var modalScope = $rootScope.$new();

                $modal.open({
                    template: '<zem-custom-audiences-modal></zem-custom-audiences-modal>',
                    controller: ['$scope', '$modalInstance', function ($scope, $modalInstance) {
                        $scope.closeModal = $modalInstance.close;
                    }],
                    windowClass: 'modal-zem-custom-audiences',
                    scope: modalScope,
                });
            });
        },
        controller: [function () {}],
    };
}]);
