var commonHelpers = require('../../../../shared/helpers/common.helpers');
var RoutePathName = require('../../../../app.constants').RoutePathName;
var ENTITY_MANAGER_CONFIG = require('../../../../features/entity-manager/entity-manager.config')
    .ENTITY_MANAGER_CONFIG;

angular.module('one.widgets').component('zemCreateEntityAction', {
    template: require('./zemCreateEntityAction.component.html'),
    bindings: {
        parentEntity: '<',
    },
    controller: function(NgRouter, $location, zemCreateEntityActionService) {
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
            callback: function() {
                createContentAds();
            },
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
            var urlTree = [
                RoutePathName.APP_BASE,
                RoutePathName.NEW_ENTITY_ANALYTICS_MOCK,
            ];

            var levelParam =
                constants.levelToLevelParamMap[
                    constants.entityTypeToLevelMap[$ctrl.entityType]
                ];
            if (commonHelpers.isDefined(levelParam)) {
                urlTree.push(levelParam);
            }

            if (commonHelpers.isDefined($ctrl.parentEntity)) {
                urlTree.push($ctrl.parentEntity.id);
            }

            var queryParams = $location.search();
            queryParams[ENTITY_MANAGER_CONFIG.typeQueryParam] =
                $ctrl.entityType;
            queryParams[ENTITY_MANAGER_CONFIG.idQueryParam] = $ctrl.parentEntity
                ? $ctrl.parentEntity.id
                : null;

            NgRouter.navigate(urlTree, {
                queryParams: queryParams,
            }).then(function() {
                NgRouter.navigate(
                    [{outlets: {drawer: ENTITY_MANAGER_CONFIG.outletName}}],
                    {
                        queryParamsHandling: 'preserve',
                    }
                );
            });
        }

        function createContentAds() {
            var entityProperties = {};
            entityProperties.type = $ctrl.entityType;
            entityProperties.parent = $ctrl.parentEntity;

            $ctrl.createInProgress = true;
            zemCreateEntityActionService
                .createContentAds(entityProperties)
                .finally(function() {
                    $ctrl.createInProgress = false;
                });
        }
    },
});
