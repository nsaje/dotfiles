require('./zemCloneCampaignModal.component.less');

angular.module('one.widgets').component('zemCloneCampaignModal', {
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    template: require('./zemCloneCampaignModal.component.html'),
    controller: function(zemNavigationService, zemCloneCampaignService) {
        var $ctrl = this;

        //
        // Public
        //
        $ctrl.submit = submit;
        $ctrl.childComponentReady = childComponentReady;

        //
        // Private
        //
        $ctrl.errors = null;
        $ctrl.requestInProgress = false;

        function childComponentReady($event) {
            $ctrl.campaignCloneFormApi = $event;
        }

        function submit() {
            $ctrl.requestInProgress = true;
            $ctrl.campaignCloneFormApi
                .executeClone()
                .then(
                    function(newCampaign) {
                        reloadCache(newCampaign);
                        zemCloneCampaignService.openResultsModal(newCampaign);
                        $ctrl.modalInstance.close();
                    },
                    function(errors) {
                        $ctrl.errors = errors;
                    }
                )
                .finally(function() {
                    $ctrl.requestInProgress = false;
                });
        }

        function reloadCache(entity) {
            // FIXME: Legacy workaround - When navigation service will be completely removed
            // this should be done automatically by listening entity services
            zemNavigationService.reloadCampaign(entity.id);
        }
    },
});
