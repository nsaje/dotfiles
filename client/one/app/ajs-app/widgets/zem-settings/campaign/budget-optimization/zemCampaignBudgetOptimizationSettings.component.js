angular
    .module('one.widgets')
    .component('zemCampaignBudgetOptimizationSettings', {
        bindings: {
            entity: '<',
            errors: '<',
            api: '<',
        },
        template: require('./zemCampaignBudgetOptimizationSettings.component.html'),
        controller: function($q) {
            var $ctrl = this;

            $ctrl.originalBudgetOptimizationState = false;

            var BUDGET_OPTIMIZATION_ENABLE_WARNING_MESSAGE =
                "Once campaign budget optimization is enabled, ad groups' " +
                "flight time settings will be reset and won't be respected " +
                'anymore. Budget flight time will be used for running ' +
                "campaign's ad groups. Additionally, daily spend caps and " +
                'bids settings will be disabled.\n\nAre you sure you want to ' +
                'enable campaign budget optimization?';
            var BUDGET_OPTIMIZATION_DISABLE_WARNING_MESSAGE =
                'You are about to disable campaign budget optimization. ' +
                "Please check ad groups' flight times, daily spend caps and " +
                'bids settings after settings are saved.\n\nAre you ' +
                'sure you want to disable campaign budget optimization?';

            $ctrl.$onInit = function() {
                $ctrl.api.register({
                    validate: validate,
                });
            };

            $ctrl.$onChanges = function() {
                if ($ctrl.entity && $ctrl.entity.settings) {
                    $ctrl.originalBudgetOptimizationState =
                        $ctrl.entity.settings.autopilot;
                }
            };

            function validate(updateData) {
                if (
                    $ctrl.originalBudgetOptimizationState ===
                    updateData.settings.autopilot
                ) {
                    return $q.resolve();
                }

                var message;
                if (updateData.settings.autopilot) {
                    message = BUDGET_OPTIMIZATION_ENABLE_WARNING_MESSAGE;
                } else {
                    message = BUDGET_OPTIMIZATION_DISABLE_WARNING_MESSAGE;
                }

                // eslint-disable-next-line no-alert
                if (confirm(message)) {
                    return $q.resolve();
                }
                $ctrl.entity.settings.autopilot =
                    $ctrl.originalBudgetOptimizationState;
                return $q.reject();
            }
        },
    });
