angular.module('one.widgets').component('zemCreateEntityAction', {
    template: require('./zemCreateEntityAction.component.html'),
    bindings: {
        parentEntity: '<',
    },
    controller: function(
        $state,
        $location,
        $uibModal,
        zemCreateEntityActionService,
        zemToastsService,
        zemNavigationNewService,
        zemPermissions
    ) {
        var $ctrl = this;
        var activeAccount = zemNavigationNewService.getActiveAccount();
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
                if (
                    zemPermissions.hasPermission(
                        'zemauth.can_use_new_account_settings_drawer'
                    )
                ) {
                    navigateToEntityCreation();
                } else {
                    createEntity();
                }
            },
        };
        MAIN_ACTIONS[constants.entityType.CAMPAIGN] = {
            name: 'Campaign',
            callback: function() {
                if (
                    zemPermissions.hasPermission(
                        'zemauth.can_use_new_campaign_settings_drawer'
                    )
                ) {
                    navigateToEntityCreation();
                } else {
                    showCampaignCreatorModal();
                }
            },
        };
        MAIN_ACTIONS[constants.entityType.AD_GROUP] = {
            name: 'Ad group',
            callback: function() {
                if (
                    zemPermissions.hasPermission(
                        'zemauth.can_use_new_ad_group_settings_drawer'
                    )
                ) {
                    navigateToEntityCreation();
                } else {
                    createEntity();
                }
            },
        };
        MAIN_ACTIONS[constants.entityType.CONTENT_AD] = {
            name: 'Content Ads',
            callback: createEntity,
        };

        var ADDITIONAL_ACTIONS = {};
        if (
            zemPermissions.hasPermission(
                'zemauth.can_create_campaign_via_campaign_launcher'
            )
        ) {
            ADDITIONAL_ACTIONS[constants.entityType.CAMPAIGN] = [
                {name: 'Launch campaign', callback: openCampaignLauncher},
            ];
        }

        $ctrl.createInProgress = false;

        $ctrl.$onInit = function() {
            $ctrl.entityType =
                $ctrl.parentEntity && $ctrl.parentEntity.type
                    ? MAP_PARENT_TYPE[$ctrl.parentEntity.type]
                    : constants.entityType.ACCOUNT;

            $ctrl.mainAction = MAIN_ACTIONS[$ctrl.entityType];
            $ctrl.additionalActions =
                ADDITIONAL_ACTIONS[$ctrl.entityType] || [];
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

        function createCampaign(campaignType) {
            createEntity({campaignType: campaignType});
        }

        function showCampaignCreatorModal() {
            if (
                !zemPermissions.hasPermission(
                    'zemauth.fea_can_change_campaign_type'
                )
            ) {
                return createCampaign(constants.campaignTypes.CONTENT);
            }

            var campaignType$ = $uibModal.open({
                // Use a proxy component in order to be able to use downgraded zem-campaign-creator-modal component
                controllerAs: '$ctrl',
                template:
                    '<zem-campaign-creator-modal class="zem-campaign-creator-modal" (on-close)="$ctrl.close($event)"></zem-campaign-creator-modal>',
                controller: function($uibModalInstance) {
                    this.close = $uibModalInstance.close;
                },
                windowClass: 'zem-campaign-creator-uib-modal',
            }).result;

            campaignType$.then(createCampaign);
        }

        function openCampaignLauncher() {
            var url = $state.href('v2.campaignLauncher', {
                id: activeAccount.id,
            });
            $location.url(url);
        }
    },
});
