var ENTITY_MANAGER_CONFIG = require('../../../../../features/entity-manager/entity-manager.config')
    .ENTITY_MANAGER_CONFIG;
var commonHelpers = require('../../../../../shared/helpers/common.helpers');
var EntityPermissionValue = require('../../../../../core/users/users.constants')
    .EntityPermissionValue;

angular.module('one.widgets').component('zemInfoboxHeader', {
    bindings: {
        entity: '<',
    },
    template: require('./zemInfoboxHeader.component.html'),
    controller: function(
        $location,
        NgRouter,
        zemEntityService,
        zemNavigationService,
        zemAuthStore
    ) {
        // eslint-disable-line max-len
        var $ctrl = this;

        $ctrl.openSettings = openSettings;
        $ctrl.toggleEntityState = toggleEntityState;

        $ctrl.$onChanges = function(changes) {
            if (changes.entity) {
                updateView(changes.entity.currentValue);
            }
        };

        function openSettings() {
            var queryParams = $location.search();
            queryParams[ENTITY_MANAGER_CONFIG.typeQueryParam] =
                $ctrl.entity.type;
            queryParams[ENTITY_MANAGER_CONFIG.idQueryParam] = $ctrl.entity.id;

            NgRouter.navigate(
                [{outlets: {drawer: ENTITY_MANAGER_CONFIG.outletName}}],
                {
                    queryParams: queryParams,
                }
            );
        }

        function updateView(entity) {
            $ctrl.isEntityAvailable = false;
            $ctrl.level = null;
            $ctrl.entityName = null;
            $ctrl.isStateSwitchAvailable = false;
            $ctrl.isStateSwitchDisabled = false;
            $ctrl.isEntityEnabled = false;

            if (!commonHelpers.isDefined(entity)) {
                // All accounts level
                $ctrl.level = getLevelFromEntity(entity);
            } else if (entity) {
                $ctrl.isEntityAvailable = true;
                $ctrl.level = getLevelFromEntity(entity);
                $ctrl.entityName = entity.name;
                if (entity.type === constants.entityType.AD_GROUP) {
                    $ctrl.isStateSwitchAvailable = true;
                    var account = entity.parent.parent;
                    $ctrl.isStateSwitchDisabled = zemAuthStore.hasReadOnlyAccessOn(
                        account.data.agencyId,
                        account.id
                    );
                }
                $ctrl.isEntityEnabled =
                    entity.data.state === constants.settingsState.ACTIVE;
            }
        }

        function getLevelFromEntity(entity) {
            if (!commonHelpers.isDefined(entity)) {
                var canUserSeeAllAccounts = zemAuthStore.hasPermissionOnAllEntities(
                    EntityPermissionValue.READ,
                    'zemauth.can_see_all_accounts'
                );
                if (canUserSeeAllAccounts) {
                    return 'All accounts';
                }
                return 'My accounts';
            }

            switch (entity.type) {
                case constants.entityType.ACCOUNT:
                    return 'Account';
                case constants.entityType.CAMPAIGN:
                    return 'Campaign';
                case constants.entityType.AD_GROUP:
                    return 'Ad Group';
            }
        }

        var requestInProgress = false;
        function toggleEntityState() {
            if (requestInProgress || $ctrl.isStateSwitchDisabled) return;

            requestInProgress = true;
            $ctrl.isEntityEnabled = !$ctrl.isEntityEnabled;
            var action =
                $ctrl.entity.data.state === constants.settingsState.ACTIVE
                    ? constants.entityAction.DEACTIVATE
                    : constants.entityAction.ACTIVATE;
            zemEntityService
                .executeAction(action, $ctrl.entity.type, $ctrl.entity.id)
                .then(function(response) {
                    zemNavigationService.reloadAdGroup(response.data.id);
                })
                .catch(function() {
                    $ctrl.isEntityEnabled = !$ctrl.isEntityEnabled;
                })
                .finally(function() {
                    requestInProgress = false;
                });
        }
    },
});
