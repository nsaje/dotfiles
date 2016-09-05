/* globals angular */
'use strict';

angular.module('one.legacy').directive('zemCustomAudiencesModalTrigger', ['$uibModal', '$rootScope', function ($uibModal, $rootScope) { // eslint-disable-line max-len
    return {
        restrict: 'A',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        link: function (scope, element, attrs, ctrl) {
            element.on('click', function () {
                var modalScope = $rootScope.$new();

                $uibModal.open({
                    template: '<zem-custom-audiences-modal></zem-custom-audiences-modal>',
                    controller: ['$scope', function ($scope) {
                        $scope.closeModal = $scope.$close;
                    }],
                    windowClass: 'modal-zem-custom-audiences',
                    scope: modalScope,
                });
            });
        },
        controller: [function () {}],
    };
}]);
