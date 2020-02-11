var ENTITY_MANAGER_CONFIG = require('../../../../../features/entity-manager/entity-manager.config')
    .ENTITY_MANAGER_CONFIG;

angular.module('one.widgets').component('zemInfoboxHeader', {
    bindings: {
        entity: '<',
    },
    template: require('./zemInfoboxHeader.component.html'),
    controller: function(
        $timeout,
        $location,
        zemEntityService,
        zemNavigationService,
        zemPermissions
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
            $location
                .search(ENTITY_MANAGER_CONFIG.settingsQueryParam, true)
                .replace();
        }

        function updateView(entity) {
            $ctrl.isEntityAvailable = false;
            $ctrl.level = null;
            $ctrl.entityName = null;
            $ctrl.isStateSwitchAvailable = false;
            $ctrl.isEntityEnabled = false;

            if (entity === null) {
                // All accounts level
                $ctrl.level = getLevelFromEntity(entity);
            } else if (entity) {
                $ctrl.isEntityAvailable = true;
                $ctrl.level = getLevelFromEntity(entity);
                $ctrl.entityName = entity.name;
                $ctrl.isStateSwitchAvailable =
                    entity.type === constants.entityType.AD_GROUP;
                $ctrl.isEntityEnabled =
                    entity.data.state === constants.settingsState.ACTIVE;
            }
        }

        function getLevelFromEntity(entity) {
            if (!entity) {
                if (
                    zemPermissions.hasPermission('zemauth.can_see_all_accounts')
                ) {
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
            if (requestInProgress) return;

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
