angular.module('one.widgets').component('zemCreateEntityAction', {
    template: require('./zemCreateEntityAction.component.html'),
    bindings: {
        parentEntity: '<',
    },
    controller: function (zemCreateEntityActionService, zemToastsService) {
        var $ctrl = this;
        var MAP_PARENT_TYPE = {};
        MAP_PARENT_TYPE[constants.entityType.ACCOUNT] = constants.entityType.CAMPAIGN;
        MAP_PARENT_TYPE[constants.entityType.CAMPAIGN] = constants.entityType.AD_GROUP;
        MAP_PARENT_TYPE[constants.entityType.AD_GROUP] = constants.entityType.CONTENT_AD;

        var MAP_ACTION_NAME = {};
        MAP_ACTION_NAME[constants.entityType.ACCOUNT] = 'Account';
        MAP_ACTION_NAME[constants.entityType.CAMPAIGN] = 'Campaign';
        MAP_ACTION_NAME[constants.entityType.AD_GROUP] = 'Ad group';
        MAP_ACTION_NAME[constants.entityType.CONTENT_AD] = 'Content Ads';

        $ctrl.createInProgress = false;
        $ctrl.createEntity = createEntity;

        $ctrl.$onInit = function () {
            $ctrl.entityType = $ctrl.parentEntity && $ctrl.parentEntity.type ?
                MAP_PARENT_TYPE[$ctrl.parentEntity.type] : constants.entityType.ACCOUNT;

            $ctrl.actionName = MAP_ACTION_NAME[$ctrl.entityType];
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
    },
});
