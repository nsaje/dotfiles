angular.module('one.widgets').component('zemCreateEntityAction', {
    template: require('./zemCreateEntityAction.component.html'),
    bindings: {
        parentEntity: '<',
    },
    controller: function(
        $state,
        $location,
        zemCreateEntityActionService,
        zemToastsService
    ) {
        var $ctrl = this;
        var MAP_PARENT_TYPE = {};
        MAP_PARENT_TYPE[constants.entityType.ACCOUNT] =
            constants.entityType.CAMPAIGN;
        MAP_PARENT_TYPE[constants.entityType.CAMPAIGN] =
            constants.entityType.AD_GROUP;
        MAP_PARENT_TYPE[constants.entityType.AD_GROUP] =
            constants.entityType.CONTENT_AD;

        var MAIN_ACTIONS = {};
        MAIN_ACTIONS[constants.entityType.ACCOUNT] = {
            name: 'Account',
            callback: function() {
                navigateToEntityCreation();
            },
        };
        MAIN_ACTIONS[constants.entityType.CAMPAIGN] = {
            name: 'Campaign',
            callback: function() {
                navigateToEntityCreation();
            },
        };
        MAIN_ACTIONS[constants.entityType.AD_GROUP] = {
            name: 'Ad group',
            callback: function() {
                navigateToEntityCreation();
            },
        };
        MAIN_ACTIONS[constants.entityType.CONTENT_AD] = {
            name: 'Content Ads',
            callback: createEntity,
        };

        $ctrl.createInProgress = false;

        $ctrl.$onInit = function() {
            $ctrl.entityType =
                $ctrl.parentEntity && $ctrl.parentEntity.type
                    ? MAP_PARENT_TYPE[$ctrl.parentEntity.type]
                    : constants.entityType.ACCOUNT;

            $ctrl.mainAction = MAIN_ACTIONS[$ctrl.entityType];
        };

        function navigateToEntityCreation() {
            var url = $state.href('v2.createEntity', {
                level:
                    constants.levelToLevelStateParamMap[
                        constants.entityTypeToLevelMap[$ctrl.entityType]
                    ],
                id: $ctrl.parentEntity ? $ctrl.parentEntity.id : null,
            });
            $location.url(url);
        }

        function createEntity(entityProperties) {
            entityProperties = entityProperties || {};
            entityProperties.type = $ctrl.entityType;
            entityProperties.parent = $ctrl.parentEntity;

            $ctrl.createInProgress = true;
            zemCreateEntityActionService
                .createEntity(entityProperties)
                .catch(function(data) {
                    zemToastsService.error(data.data.data, {timeout: 7000});
                })
                .finally(function() {
                    $ctrl.createInProgress = false;
                });
        }
    },
});
