angular.module('one.widgets').component('zemCloneCampaignSuccessfulModal', {
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    template: require('./zemCloneCampaignSuccessfulModal.component.html'),
    controller: function(zemNavigationNewService) {
        var $ctrl = this;

        $ctrl.navigateTo = navigateTo;

        function navigateTo() {
            $ctrl.modalInstance.close();
            return zemNavigationNewService
                .getEntityById(
                    constants.entityType.CAMPAIGN,
                    $ctrl.resolve.campaign.id
                )
                .then(function(navigationEntity) {
                    zemNavigationNewService.navigateTo(navigationEntity);
                });
        }
    },
});
