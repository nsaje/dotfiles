angular.module('one.widgets').component('zemInfoboxHeader', {
    bindings: {
        entity: '<',
    },
    templateUrl: '/app/widgets/zem-infobox/components/zem-infobox-header/zemInfoboxHeader.component.html',
    controller: function ($timeout, zemSettingsService, zemEntityService, zemNavigationService) {
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
            if (!entity) return 'All Accounts';

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
                    errorMessageFadeInAndOut(error.data.message);
                })
                .finally(function () {
                    requestInProgress = false;
                });
        }

        function errorMessageFadeInAndOut (message) {
            $ctrl.errorMessage = message;
            $ctrl.errorMessageVisible = true;
            $timeout(function () {
                $ctrl.errorMessageVisible = false;
                // Wait for fade-out animation to finish
                $timeout(function () {
                    $ctrl.errorMessage = null;
                }, 200);
            }, 5000);
        }
    },
});
