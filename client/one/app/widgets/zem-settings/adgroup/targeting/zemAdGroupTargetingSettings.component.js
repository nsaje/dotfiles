angular.module('one.widgets').component('zemAdGroupTargetingSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/adgroup/targeting/zemAdGroupTargetingSettings.component.html',
    controller: ['$q', 'config', 'zemPermissions', function ($q, config, zemPermissions) {
        var $ctrl = this;
        $ctrl.options = options;
        $ctrl.config = config;
        $ctrl.constants = constants;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.retargetingEnabled = false;
        $ctrl.getTargetingWarningMessage = getTargetingWarningMessage;

        $ctrl.$onInit = function () {
            $ctrl.api.register({
                // Not needed (placeholder)
            });
        };

        $ctrl.$onChanges = function () {
            $ctrl.retargetingEnabled = isRetargetingEnabled();
        };

        function getTargetingWarningMessage () {
            if ($ctrl.entity.warnings && $ctrl.entity.warnings.retargeting !== undefined) {
                var text = 'You have some active media sources that ' +
                    'don\'t support retargeting. ' +
                    'To start using it please disable/pause these media sources:';
                var sourcesText = $ctrl.entity.warnings.retargeting.sources.join(', ');

                return text + ' ' + sourcesText + '.';
            }
            return null;
        }

        function isRetargetingEnabled () {
            var settings = $ctrl.entity.settings;
            if (!$ctrl.hasPermission('zemauth.can_target_custom_audiences')
                && settings.retargetingAdGroups && !!settings.retargetingAdGroups.length) {
                return true;
            }

            if ((settings.retargetingAdGroups && !!settings.retargetingAdGroups.length) ||
                (settings.exclusionRetargetingAdGroups && !!settings.exclusionRetargetingAdGroups.length) ||
                (settings.audienceTargeting && !!settings.audienceTargeting.length) ||
                (settings.exclusionAudienceTargeting && !!settings.exclusionAudienceTargeting.length)) {
                return true;
            }

            return false;
        }
    }],
});
