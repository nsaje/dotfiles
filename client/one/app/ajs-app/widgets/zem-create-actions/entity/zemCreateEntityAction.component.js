angular.module('one.widgets').component('zemCreateEntityAction', {
    template: require('./zemCreateEntityAction.component.html'),
    bindings: {
        parentEntity: '<',
    },
    controller: function ($state, $location, zemCreateEntityActionService, zemToastsService, zemNavigationNewService, zemPermissions) { // eslint-disable-line max-len
        var $ctrl = this;
        var activeAccount = zemNavigationNewService.getActiveAccount();
        var MAP_PARENT_TYPE = {};
        MAP_PARENT_TYPE[constants.entityType.ACCOUNT] = constants.entityType.CAMPAIGN;
        MAP_PARENT_TYPE[constants.entityType.CAMPAIGN] = constants.entityType.AD_GROUP;
        MAP_PARENT_TYPE[constants.entityType.AD_GROUP] = constants.entityType.CONTENT_AD;

        var MAIN_ACTIONS = {};
        MAIN_ACTIONS[constants.entityType.ACCOUNT] = {name: 'Account', callback: createEntity};
        MAIN_ACTIONS[constants.entityType.CAMPAIGN] = {name: 'Campaign', callback: createEntity};
        MAIN_ACTIONS[constants.entityType.AD_GROUP] = {name: 'Ad group', callback: createEntity};
        MAIN_ACTIONS[constants.entityType.CONTENT_AD] = {name: 'Content Ads', callback: createEntity};

        var ADDITIONAL_ACTIONS = {};
        if (zemPermissions.hasPermission('zemauth.can_create_campaign_via_campaign_launcher')) {
            ADDITIONAL_ACTIONS[constants.entityType.CAMPAIGN] = [
                {name: 'Launch campaign', callback: openCampaignLauncher},
            ];
        }

        $ctrl.createInProgress = false;
        $ctrl.createEntity = createEntity;

        $ctrl.$onInit = function () {
            $ctrl.entityType = $ctrl.parentEntity && $ctrl.parentEntity.type ?
                MAP_PARENT_TYPE[$ctrl.parentEntity.type] : constants.entityType.ACCOUNT;

            $ctrl.mainAction = MAIN_ACTIONS[$ctrl.entityType];
            $ctrl.additionalActions = ADDITIONAL_ACTIONS[$ctrl.entityType] || [];
        };

        function createEntity () {
            $ctrl.createInProgress = true;
            zemCreateEntityActionService
                .createEntity($ctrl.entityType, $ctrl.parentEntity)
                .catch(function (data) {
                    zemToastsService.error(data.data.data, {timeout: 7000});
                }).finally(function () {
                    $ctrl.createInProgress = false;
                });
        }

        function openCampaignLauncher () {
            var url = $state.href('v2.campaignLauncher', {id: activeAccount.id});
            $location.url(url);
        }
    },
});
