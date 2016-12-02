angular.module('one.widgets').component('zemAdGroupAutopilotSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/adgroup/autopilot/zemAdGroupAutopilotSettings.component.html',
    controller: function ($q, config, zemPermissions) {
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
                // Not needed (placeholder)
            });
        };

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
