/*globals angular*/
'use strict';

angular.module('one.widgets').component('zemCustomAudiencesList', {
    templateUrl: '/app/widgets/zem-custom-audiences/components/list/zemCustomAudiencesList.component.html',
    bindings: {
        stateService: '<',
    },
    controller: function (zemDataFilterService, zemPermissions, $scope, $uibModal) {
        var $ctrl = this;

        $ctrl.$onInit = function () {
            $ctrl.state = $ctrl.stateService.getState();
            $ctrl.restoreAudience = $ctrl.stateService.restore;
            $ctrl.archiveAudience = $ctrl.stateService.archive;
            $ctrl.openAudienceModal = openAudienceModal;
        };

        function openAudienceModal (audience) {
            $uibModal.open({
                component: 'zemCustomAudiencesModal',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    stateService: $ctrl.stateService,
                    audience: audience,
                },
            });
        }
    }
});
