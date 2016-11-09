angular.module('one.widgets').component('zemAdGroupTargetingSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/adgroup/targeting/zemAdGroupTargetingSettings.component.html',
    controller: function ($q, config, zemPermissions) {
        var $ctrl = this;
        $ctrl.options = options;
        $ctrl.config = config;
        $ctrl.constants = constants;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.retargetingEnabled = false;
        $ctrl.getTargetingWarningMessage = getTargetingWarningMessage;
        $ctrl.addTargeting = addTargeting;
        $ctrl.removeTargeting = removeTargeting;

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

        function addTargeting (type, id) {
            if (type === 'adGroupTargeting') {
                if (!$ctrl.entity.settings.retargetingAdGroups) {
                    $ctrl.entity.settings.retargetingAdGroups = [];
                }
                $ctrl.entity.settings.retargetingAdGroups.push(id);
            } else if (type === 'exclusionAdGroupTargeting') {
                if (!$ctrl.entity.settings.exclusionRetargetingAdGroups) {
                    $ctrl.entity.settings.exclusionRetargetingAdGroups = [];
                }
                $ctrl.entity.settings.exclusionRetargetingAdGroups.push(id);
            } else if (type === 'audienceTargeting') {
                if (!$ctrl.entity.settings.audienceTargeting) {
                    $ctrl.entity.settings.audienceTargeting = [];
                }
                $ctrl.entity.settings.audienceTargeting.push(id);
            } else if (type === 'exclusionAudienceTargeting') {
                if (!$ctrl.entity.settings.exclusionAudienceTargeting) {
                    $ctrl.entity.settings.exclusionAudienceTargeting = [];
                }
                $ctrl.entity.settings.exclusionAudienceTargeting.push(id);
            }
        }

        function removeTargeting (type, id) {
            var index = -1;
            if (type === 'adGroupTargeting' && $ctrl.entity.settings.retargetingAdGroups) {
                index = $ctrl.entity.settings.retargetingAdGroups.indexOf(id);
                if (index >= 0) {
                    $ctrl.entity.settings.retargetingAdGroups.splice(index, 1);
                }
            } else if (type === 'exclusionAdGroupTargeting' && $ctrl.entity.settings.exclusionRetargetingAdGroups) {
                index = $ctrl.entity.settings.exclusionRetargetingAdGroups.indexOf(id);
                if (index >= 0) {
                    $ctrl.entity.settings.exclusionRetargetingAdGroups.splice(index, 1);
                }
            } else if (type === 'audienceTargeting' && $ctrl.entity.settings.audienceTargeting) {
                index = $ctrl.entity.settings.audienceTargeting.indexOf(id);
                if (index >= 0) {
                    $ctrl.entity.settings.audienceTargeting.splice(index, 1);
                }
            } else if (type === 'exclusionAudienceTargeting' && $ctrl.entity.settings.exclusionAudienceTargeting) {
                index = $ctrl.entity.settings.exclusionAudienceTargeting.indexOf(id);
                if (index >= 0) {
                    $ctrl.entity.settings.exclusionAudienceTargeting.splice(index, 1);
                }
            }
        }
    },
});
