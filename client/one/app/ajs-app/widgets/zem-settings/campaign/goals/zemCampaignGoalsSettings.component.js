angular.module('one.widgets').component('zemLegacyCampaignGoalsSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    template: require('./zemCampaignGoalsSettings.component.html'),
    controller: function($q, zemPermissions, zemNavigationNewService) {
        // eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.options = options;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.entityGoalsDiff = {};
        $ctrl.validateGoals = validateGoals;

        $ctrl.$onInit = function() {
            $ctrl.account = zemNavigationNewService.getActiveAccount();
            $ctrl.api.register({
                validate: validate,
                onSuccess: clear,
            });
        };

        function validate(updateData) {
            if (validateGoals()) {
                updateData.goals = $ctrl.entityGoalsDiff;
                return $q.resolve();
            }

            return $q.reject();
        }

        function clear() {
            $ctrl.entityGoalsDiff.added = [];
            $ctrl.entityGoalsDiff.removed = [];
            $ctrl.entityGoalsDiff.primary = null;
            $ctrl.entityGoalsDiff.modified = {};
        }

        function validateGoals() {
            var primary = false,
                goals = $ctrl.entity.goals;
            if (!goals || !goals.length) {
                return true;
            }
            goals.forEach(function(goal) {
                if (goal.primary) {
                    primary = true;
                }
            });
            if (!primary) {
                if (!$ctrl.errors) $ctrl.errors = {};
                $ctrl.errors.goals = ['One goal has to be set as primary.'];
            }
            return primary;
        }
    },
});
