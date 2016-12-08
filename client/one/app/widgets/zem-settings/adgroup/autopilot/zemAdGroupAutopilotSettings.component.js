angular.module('one.widgets').component('zemAdGroupAutopilotSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/adgroup/autopilot/zemAdGroupAutopilotSettings.component.html',
    controller: function ($q, $state, config, zemPermissions) {
        var MSG_ALL_RTB_ENABLED = 'All RTB source will now use one joint Daily Spend Cap.\n\n' +
            'Please check it in the Media Sources tab before you enable the ad group.\n';
        var MSG_ALL_RTB_DISABLED = 'We have reset the Daily Spend Caps of your RTB sources.\n\n' +
            'Please check them in the Media Sources tab before you enable the ad group.\n';

        var $ctrl = this;
        $ctrl.constants = constants;
        $ctrl.config = config;
        $ctrl.options = options;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.isInLanding = isInLanding;
        $ctrl.showAutoPilotDailyBudgetInput = showAutoPilotDailyBudgetInput;
        $ctrl.getBudgetAutopilotOptimizationGoalText = getBudgetAutopilotOptimizationGoalText;
        $ctrl.getBudgetAutopilotOptimizationCPAGoalText = getBudgetAutopilotOptimizationCPAGoalText;

        $ctrl.$onInit = function () {
            $ctrl.api.register({
                onSuccess: function () {
                    notifyAllRtbUpdates();
                }
            });
        };

        $ctrl.$onChanges = function () {
            if ($ctrl.entity) {
                $ctrl.origAutopilotSettings = {
                    b1SourcesGroupEnabled: $ctrl.entity.settings.b1SourcesGroupEnabled,
                    autopilotState: $ctrl.entity.settings.autopilotState,
                    autopilotBudget: $ctrl.entity.settings.autopilotBudget,
                };
            }
        };

        function notifyAllRtbUpdates () {
            // MVP for all-RTB-sources-as-one
            // Reload state when all-rtb-as-one setting is changed (grid data representation changes)
            var allRtbAsOne = $ctrl.entity.settings.b1SourcesGroupEnabled &&
                      $ctrl.entity.settings.autopilotState ===
                      constants.adGroupSettingsAutopilotState.INACTIVE;

            var origAllRtbAsOne = $ctrl.origAutopilotSettings.b1SourcesGroupEnabled &&
                       $ctrl.origAutopilotSettings.autopilotState ===
                       constants.adGroupSettingsAutopilotState.INACTIVE;


            if (allRtbAsOne !== origAllRtbAsOne) {
                alert(allRtbAsOne ? MSG_ALL_RTB_ENABLED : MSG_ALL_RTB_DISABLED); //eslint-disable-line no-alert
                $state.reload();
            }
        }

        function isInLanding () {
            if (!$ctrl.entity) return false;
            return $ctrl.entity.settings.landingMode;
        }

        function showAutoPilotDailyBudgetInput () {
            if (!$ctrl.entity) return false;
            return $ctrl.entity.settings.autopilotState === constants.adGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET;
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
    },
});
