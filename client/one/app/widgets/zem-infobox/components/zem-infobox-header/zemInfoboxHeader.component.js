angular.module('one.widgets').component('zemInfoboxHeader', {
    bindings: {
        entity: '<',
    },
    templateUrl: '/app/widgets/zem-infobox/components/zem-infobox-header/zemInfoboxHeader.component.html',
    controller: function ($timeout, zemSettingsService, zemEntityService, zemNavigationService, zemPermissions, zemToastsService) { // eslint-disable-line max-len
        var $ctrl = this;

        $ctrl.openSettings = zemSettingsService.open;
        $ctrl.toggleEntityState = toggleEntityState;

        $ctrl.$onChanges = function (changes) {
            if (changes.entity) {
                updateView(changes.entity.currentValue);
            }
        };

        function updateView (entity) {
            $ctrl.isEntityAvailable = false;
            $ctrl.level = null;
            $ctrl.entityName = null;
            $ctrl.isStateSwitchAvailable = false;
            $ctrl.isEntityEnabled = false;

            if (entity === null) { // All accounts level
                $ctrl.level = getLevelFromEntity(entity);
            } else if (entity) {
                $ctrl.isEntityAvailable = true;
                $ctrl.level = getLevelFromEntity(entity);
                $ctrl.entityName = entity.name;
                $ctrl.isStateSwitchAvailable = entity.type === constants.entityType.AD_GROUP;
                $ctrl.isEntityEnabled = entity.data.state === constants.settingsState.ACTIVE;
            }
        }

        function getLevelFromEntity (entity) {
            if (!entity) {
                if (zemPermissions.hasPermission('dash.group_account_automatically_add')) {
                    return 'All accounts';
                }
                return 'My accounts';
            }

            switch (entity.type) {
            case constants.entityType.ACCOUNT: return 'Account';
            case constants.entityType.CAMPAIGN: return 'Campaign';
            case constants.entityType.AD_GROUP: return 'Ad Group';
            }
        }

        var requestInProgress = false;
        function toggleEntityState () {
            if (requestInProgress) return;

            requestInProgress = true;
            $ctrl.isEntityEnabled = !$ctrl.isEntityEnabled;
            var action = $ctrl.entity.data.state === constants.settingsState.ACTIVE ?
                constants.entityAction.DEACTIVATE : constants.entityAction.ACTIVATE;
            zemEntityService.executeAction(action, $ctrl.entity.type, $ctrl.entity.id)
                .then(function (response) {
                    zemNavigationService.reloadAdGroup(response.data.id);
                })
                .catch(function (error) {
                    $ctrl.isEntityEnabled = !$ctrl.isEntityEnabled;
                    zemToastsService.error(error.data.message, {timeout: 5000});
                })
                .finally(function () {
                    requestInProgress = false;
                });
        }
    },
});
