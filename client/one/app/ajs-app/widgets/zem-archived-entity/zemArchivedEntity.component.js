angular.module('one').component('zemArchivedEntity', {
    bindings: {
        entity: '<',
    },
    template: require('./zemArchivedEntity.component.html'),
    controller: function(
        zemEntityService,
        zemNavigationNewService,
        zemNavigationService
    ) {
        var $ctrl = this;
        $ctrl.restore = restore;
        $ctrl.getEntityTypeName = getEntityTypeName;

        function restore() {
            $ctrl.requestInProgress = true;
            zemEntityService
                .executeAction(
                    constants.entityAction.RESTORE,
                    $ctrl.entity.type,
                    $ctrl.entity.id
                )
                .then(updateNavigationCache)
                .then(zemNavigationNewService.refreshState)
                .finally(function() {
                    $ctrl.requestInProgress = false;
                });
        }

        function updateNavigationCache() {
            // TODO - delete (this will not be needed after removing zemNavigationService)
            if ($ctrl.entity.type === constants.entityType.AD_GROUP) {
                return zemNavigationService.reloadAdGroup($ctrl.entity.id);
            }
            if ($ctrl.entity.type === constants.entityType.CAMPAIGN) {
                return zemNavigationService.reloadCampaign($ctrl.entity.id);
            }
            if ($ctrl.entity.type === constants.entityType.ACCOUNT) {
                return zemNavigationService.reloadAccount($ctrl.entity.id);
            }
        }

        function getEntityTypeName() {
            if (!$ctrl.entity) return;
            if ($ctrl.entity.type === constants.entityType.ACCOUNT)
                return 'Account';
            if ($ctrl.entity.type === constants.entityType.CAMPAIGN)
                return 'Campaign';
            if ($ctrl.entity.type === constants.entityType.AD_GROUP)
                return 'Ad Group';
        }
    },
});
