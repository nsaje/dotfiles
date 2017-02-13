angular.module('one.widgets').component('zemAdGroupModeSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/adgroup/mode/zemAdGroupModeSettings.component.html',
    controller: function ($q, $state, config, zemPermissions) {
        var MSG_ALL_RTB_ENABLED = 'This ad group will be automatically paused to set one joint Daily Spend Cap for ' +
            'all RTB sources. Please check it in the Media Sources tab before enabling the ad group.';
        var MSG_ALL_RTB_DISABLED = 'This ad group will be automatically paused to reset the Daily Spend Caps of ' +
            'all RTB sources. Please check them in the Media Sources tab before you enable the ad group.';

        var $ctrl = this;
        $ctrl.constants = constants;
        $ctrl.config = config;
        $ctrl.options = options;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.isInLanding = isInLanding;
        $ctrl.isAutomaticMode = isAutomaticMode;
        $ctrl.setToManualMode = setToManualMode;
        $ctrl.updateModeSettings = updateModeSettings;

        $ctrl.getBudgetAutopilotOptimizationGoalText = getBudgetAutopilotOptimizationGoalText;
        $ctrl.getBudgetAutopilotOptimizationCPAGoalText = getBudgetAutopilotOptimizationCPAGoalText;

        $ctrl.$onInit = function () {
            $ctrl.api.register({
                validate: validate,
            });
        };

        $ctrl.$onChanges = function () {
            if (!$ctrl.entity || ($ctrl.origAdGroupModeSettings && $ctrl.prevAdGroupModeSettings)) return;
            $ctrl.origAdGroupModeSettings = {
                b1SourcesGroupEnabled: $ctrl.entity.settings.b1SourcesGroupEnabled,
            };

            $ctrl.prevAdGroupModeSettings = {
                b1SourcesGroupEnabled: $ctrl.entity.settings.b1SourcesGroupEnabled,
                priceDiscovery: $ctrl.entity.settings.priceDiscovery,
            };

        };

        function isInLanding () {
            if (!$ctrl.entity) return false;
            return $ctrl.entity.settings.landingMode;
        }

        function isAutomaticMode () {
            if (!$ctrl.entity) return false;
            return $ctrl.entity.settings.adGroupMode === constants.adGroupMode.AUTOMATIC;
        }

        function setToManualMode () {
            $ctrl.entity.settings.adGroupMode = constants.adGroupMode.MANUAL;
            $ctrl.updateModeSettings();
        }

        function updateModeSettings () {
            if ($ctrl.entity.settings.adGroupMode === constants.adGroupMode.AUTOMATIC) {
                $ctrl.prevAdGroupModeSettings.b1SourcesGroupEnabled = $ctrl.entity.settings.b1SourcesGroupEnabled;
                $ctrl.prevAdGroupModeSettings.priceDiscovery = $ctrl.entity.settings.priceDiscovery;

                $ctrl.entity.settings.b1SourcesGroupEnabled = true;
                $ctrl.entity.settings.priceDiscovery = constants.priceDiscovery.AUTOMATIC;
            } else {
                $ctrl.entity.settings.b1SourcesGroupEnabled = $ctrl.prevAdGroupModeSettings.b1SourcesGroupEnabled;
                $ctrl.entity.settings.priceDiscovery = $ctrl.prevAdGroupModeSettings.priceDiscovery;
            }
        }

        function getBudgetAutopilotOptimizationGoalText () {
            if (!$ctrl.entity) return '';
            var goalName = 'maximum volume';
            options.budgetAutomationGoals.forEach(function (goal) {
                if (goal.value === $ctrl.entity.settings.autopilotOptimizationGoal) {
                    goalName = goal.name;
                }
            });
            return goalName;
        }

        function getBudgetAutopilotOptimizationCPAGoalText () {
            if (!$ctrl.entity) return '';
            if ($ctrl.entity.settings.autopilotOptimizationGoal !== constants.campaignGoalKPI.CPA) {
                return '';
            }
            return 'Note: CPA optimization works best when at least ' +
                '20 conversions have occurred in the past two weeks.';
        }

        function validate (updateData) {
            if (updateData.settings.state === constants.settingsState.INACTIVE) {
                return $q.resolve();
            }

            if ($ctrl.origAdGroupModeSettings.b1SourcesGroupEnabled !== updateData.settings.b1SourcesGroupEnabled) {
                if (updateData.settings.b1SourcesGroupEnabled &&
                        confirm(MSG_ALL_RTB_ENABLED)) { //eslint-disable-line no-alert
                    updateData.settings.state = constants.settingsState.INACTIVE;
                    return $q.resolve();
                } else if (confirm(MSG_ALL_RTB_DISABLED)) { //eslint-disable-line no-alert
                    updateData.settings.state = constants.settingsState.INACTIVE;
                    return $q.resolve();
                }
                return $q.reject();
            }

            return $q.resolve();
        }
    },
});
