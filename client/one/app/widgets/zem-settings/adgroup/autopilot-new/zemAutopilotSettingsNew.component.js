angular.module('one.widgets').component('zemAutopilotSettingsNew', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/adgroup/autopilot-new/zemAutopilotSettingsNew.component.html',
    controller: function ($q, $state, config, zemPermissions) {
        var MSG_ALL_RTB_ENABLED_AD_GROUP_INACTIVE = 'One joint Bid CPC and Daily Spend Cap for will be set for all ' +
            'RTB sources. Please check it in the Media Sources tab before enabling the ad group.';
        var MSG_ALL_RTB_ENABLED_AD_GROUP_ACTIVE = 'This ad group will be automatically paused to set one joint Bid ' +
            'CPC and Daily Spend Cap for all RTB sources. Please check it in the Media Sources tab before enabling ' +
            'the ad group.';
        var MSG_ALL_RTB_DISABLED_AD_GROUP_INACTIVE = 'Bid CPCs and Daily Spend Caps of all RTB sources will be ' +
            'reset. Please check them in the Media Sources tab before you enable the ad group.';
        var MSG_ALL_RTB_DISABLED_AD_GROUP_ACTIVE = 'This ad group will be automatically paused to reset the Bid CPCs ' +
            'and Daily Spend Caps of all RTB sources. Please check them in the Media Sources tab before you enable ' +
            'the ad group.';

        var $ctrl = this;
        $ctrl.constants = constants;
        $ctrl.config = config;
        $ctrl.options = options;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.isInLanding = isInLanding;
        $ctrl.updateAutopilotSettings = updateAutopilotSettings;

        $ctrl.getBudgetAutopilotOptimizationGoalText = getBudgetAutopilotOptimizationGoalText;
        $ctrl.getBudgetAutopilotOptimizationCPAGoalText = getBudgetAutopilotOptimizationCPAGoalText;

        $ctrl.getPriceDiscoveryPopoverText = getPriceDiscoveryPopoverText;
        $ctrl.getRTBSourcesPopoverText = getRTBSourcesPopoverText;

        $ctrl.autopilotEnabled = null;
        $ctrl.b1SourcesGroupEnabled = null;
        $ctrl.priceDiscovery = null;

        $ctrl.$onInit = function () {
            $ctrl.api.register({
                validate: validate,
            });
        };

        $ctrl.$onChanges = function () {
            if (!$ctrl.entity || $ctrl.origAutopilotSettings) return;
            $ctrl.origAutopilotSettings = {
                b1SourcesGroupEnabled: $ctrl.entity.settings.b1SourcesGroupEnabled,
            };

            $ctrl.b1SourcesGroupEnabled = $ctrl.entity.settings.b1SourcesGroupEnabled;
            $ctrl.autopilotEnabled =
                $ctrl.entity.settings.autopilotState === constants.adGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET;
            $ctrl.priceDiscovery = $ctrl.autopilotEnabled ||
                $ctrl.entity.settings.autopilotState === constants.adGroupSettingsAutopilotState.ACTIVE_CPC;
        };

        function isInLanding () {
            if (!$ctrl.entity) return false;
            return $ctrl.entity.settings.landingMode;
        }

        function updateAutopilotSettings () {
            $ctrl.entity.settings.b1SourcesGroupEnabled = $ctrl.b1SourcesGroupEnabled;
            $ctrl.entity.settings.autopilotState = constants.adGroupSettingsAutopilotState.INACTIVE;

            if ($ctrl.autopilotEnabled) {
                $ctrl.entity.settings.b1SourcesGroupEnabled = true;
                $ctrl.entity.settings.autopilotState = constants.adGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET;
            } else if ($ctrl.priceDiscovery) {
                $ctrl.entity.settings.autopilotState = constants.adGroupSettingsAutopilotState.ACTIVE_CPC;
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
            if (!zemPermissions.hasPermission('zemauth.can_set_ad_group_mode')) {
                return $q.resolve();
            }

            if ($ctrl.origAutopilotSettings.b1SourcesGroupEnabled === updateData.settings.b1SourcesGroupEnabled) {
                return $q.resolve();
            }

            var msg;
            if (updateData.settings.b1SourcesGroupEnabled &&
                $ctrl.entity.settings.state === constants.settingsState.INACTIVE)
                msg = MSG_ALL_RTB_ENABLED_AD_GROUP_INACTIVE;
            else if (updateData.settings.b1SourcesGroupEnabled &&
                     $ctrl.entity.settings.state === constants.settingsState.ACTIVE)
                msg = MSG_ALL_RTB_ENABLED_AD_GROUP_ACTIVE;
            else if (!updateData.settings.b1SourcesGroupEnabled &&
                     $ctrl.entity.settings.state === constants.settingsState.INACTIVE)
                msg = MSG_ALL_RTB_DISABLED_AD_GROUP_INACTIVE;
            else if (!updateData.settings.b1SourcesGroupEnabled
                     && $ctrl.entity.settings.state === constants.settingsState.ACTIVE)
                msg = MSG_ALL_RTB_DISABLED_AD_GROUP_ACTIVE;

            if (confirm(msg)) { //eslint-disable-line no-alert
                updateData.settings.state = constants.settingsState.INACTIVE;
                return $q.resolve();
            }

            return $q.reject();
        }

        function getPriceDiscoveryPopoverText () {
            if (!$ctrl.entity) return '';
            if ($ctrl.autopilotEnabled) {
                return 'You can\'t change Price Discovery while Ad Group is set to Autopilot mode.';
            }

            return '';
        }

        function getRTBSourcesPopoverText () {
            if (!$ctrl.entity) return '';
            if ($ctrl.autopilotEnabled) {
                return 'You can\'t manage RTB Sources while Ad Group is set to Autopilot mode.';
            }

            return '';
        }
    },
});
