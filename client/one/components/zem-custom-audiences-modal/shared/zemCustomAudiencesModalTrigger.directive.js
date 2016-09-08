/* globals angular */
'use strict';

angular.module('one.legacy').directive('zemCustomAudiencesModalTrigger', ['$uibModal', '$rootScope', function ($uibModal, $rootScope) { // eslint-disable-line max-len
    return {
        restrict: 'A',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            accountId: '=accountId',
            audienceId: '=audienceId',
            readonly: '=readonly',
        },
        link: function (scope, element, attrs, ctrl) {
            element.on('click', function () {
                var modalScope = $rootScope.$new();
                modalScope.accountId = ctrl.accountId;
                modalScope.audienceId = ctrl.audienceId;
                modalScope.readonly = ctrl.readonly;

                $uibModal.open({
                    template: '<zem-custom-audiences-modal account-id="accountId" audience-id="audienceId" readonly="readonly" data-close-modal="closeModal"></zem-custom-audiences-modal>',
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
