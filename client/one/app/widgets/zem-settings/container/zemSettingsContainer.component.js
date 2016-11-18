angular.module('one.widgets').component('zemSettingsContainer', {
    transclude: {
        settings: 'settings',
        custom: 'custom',
    },
    bindings: {
        title: '<',
        entityType: '<',
        entityId: '<',
    },
    templateUrl: '/app/widgets/zem-settings/container/zemSettingsContainer.component.html',
    controller: function ($transclude, $element, $q, zemPermissions, zemEntityService, zemNavigationService) { // eslint-disable-line max-len
        var STATUS_CODE_NONE = 0;
        var STATUS_CODE_IN_PROGRESS = 1;
        var STATUS_CODE_SUCCESS = 2;
        var STATUS_CODE_ERROR = 3;

        var STATUS_TEST_SAVE_SUCCESS = 'Your updates have been saved.';
        var STATUS_TEST_SAVE_ERROR = 'An error occurred while saving. Please correct the marked fields and save again.';
        var STATUS_TEST_DISCARD_SUCCESS = 'Your updates have been discarded.';

        var $ctrl = this;
        $ctrl.constants = constants;
        $ctrl.$container = this;
        var settingsComponents = [];

        $ctrl.entity = null;
        $ctrl.errors = {};
        $ctrl.status = {
            code: STATUS_CODE_NONE,
            text: ''
        };

        $ctrl.save = save;
        $ctrl.discard = discard;
        $ctrl.archive = archive;
        $ctrl.restore = restore;
        $ctrl.getButtonsBarClass = getButtonsBarClass;
        $ctrl.getEntityTypeName = getEntityTypeName;
        $ctrl.getArchiveTooltip = getArchiveTooltip;
        $ctrl.getRestoreTooltip = getRestoreTooltip;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.api = {
            register: registerSettingsComponent,
        };


        $ctrl.$postLink = function () {
        };

        $ctrl.$onInit = function () {
            load();
        };

        function load () {
            return zemEntityService.getEntity($ctrl.entityType, $ctrl.entityId).then(function (entity) {
                setEntity(entity);
            });
        }

        function registerSettingsComponent (settingsComponent) {
            // Called by settings components
            //   -> validate, onSuccess, onError
            settingsComponents.push(settingsComponent);
        }

        function setEntity (entity) {
            $ctrl.origEntity = entity;
            $ctrl.entity = angular.copy(entity);
        }

        function save () {
            var validationPromises = [];
            var updateData = {settings: $ctrl.entity.settings};
            settingsComponents.forEach(function (component) {
                if (component.validate) validationPromises.push(component.validate(updateData));
            });
            $q.all(validationPromises).then(function () {
                executeSave(updateData);
            });
        }

        function executeSave (updateData) {
            $ctrl.status.code = STATUS_CODE_IN_PROGRESS;
            zemEntityService.updateEntity($ctrl.entityType, $ctrl.entityId, updateData).then(function (entity) {
                angular.merge($ctrl.entity, entity);
                $ctrl.origEntity = angular.copy($ctrl.entity);
                $ctrl.errors = {};

                updateNavigationCache();

                $ctrl.status.code = STATUS_CODE_SUCCESS;
                $ctrl.status.text = STATUS_TEST_SAVE_SUCCESS;

                settingsComponents.forEach(function (component) {
                    if (component.onSuccess) component.onSuccess($ctrl.entity);
                });
            },
            function (data) {
                $ctrl.errors = data;
                $ctrl.status.code = STATUS_CODE_ERROR;
                $ctrl.status.text = STATUS_TEST_SAVE_ERROR;

                settingsComponents.forEach(function (component) {
                    if (component.onError) component.onError($ctrl.errors);
                });
            });
        }

        function updateNavigationCache () {
            // TODO - delete (this will not be needed after removing zemNavigationService)
            if ($ctrl.entityType === constants.entityType.ACCOUNT) {
                zemNavigationService.updateAccountCache($ctrl.entityId, {
                    name: $ctrl.entity.settings.name,
                    agency: $ctrl.entity.settings.agency.id || null,
                });
            }
            if ($ctrl.entityType === constants.entityType.CAMPAIGN) {
                zemNavigationService.updateCampaignCache($ctrl.entityId, {
                    name: $ctrl.entity.settings.name,
                });
            }
            if ($ctrl.entityType === constants.entityType.AD_GROUP) {
                zemNavigationService.reloadAdGroup($ctrl.entityId);
            }
        }

        function discard () {
            setEntity($ctrl.origEntity);
            $ctrl.status.code = STATUS_CODE_SUCCESS;
            $ctrl.status.text = STATUS_TEST_DISCARD_SUCCESS;
        }

        function archive () {
            $ctrl.status.code = STATUS_CODE_IN_PROGRESS;
            zemEntityService.executeAction(constants.entityAction.ARCHIVE, $ctrl.entityType, $ctrl.entityId)
            .then(load).then(resetStatus);
        }

        function restore () {
            $ctrl.status.code = STATUS_CODE_IN_PROGRESS;
            zemEntityService.executeAction(constants.entityAction.RESTORE, $ctrl.entityType, $ctrl.entityId)
            .then(load).then(resetStatus);
        }

        function resetStatus () {
            $ctrl.status.code = STATUS_CODE_NONE;
            $ctrl.status.text = null;
        }

        //
        // Names & Tooltips & Styles
        //
        var TOOLTIP_ARCHIVE_ACCOUNT = 'All of the account\'s campaigns have to be paused in order to archive the account.'; // eslint-disable-line max-len
        var TOOLTIP_ARCHIVE_CAMPAIGN = 'All of the campaign\'s ad groups have to be paused in order to archive the campaign.'; // eslint-disable-line max-len
        var TOOLTIP_ARCHIVE_ADGROUP = 'An ad group has to be paused for 3 days in order to archive it.';

        var TOOLTIP_RESTORE_ACCOUNT = '';
        var TOOLTIP_RESTORE_CAMPAIGN = 'In order to restore a campaign, it\'s account must be restored first.';
        var TOOLTIP_RESTORE_ADGROUP = 'An ad group has to be paused in order to archive it.';

        function getButtonsBarClass () {
            if ($ctrl.entityType === constants.entityType.ACCOUNT) return 'action-buttons-account';
            return 'action-buttons';
        }

        function getEntityTypeName () {
            if ($ctrl.entityType === constants.entityType.ACCOUNT) return 'account';
            if ($ctrl.entityType === constants.entityType.CAMPAIGN) return 'campaign';
            if ($ctrl.entityType === constants.entityType.AD_GROUP) return 'ad group';
        }

        function getArchiveTooltip () {
            if (!$ctrl.entity || $ctrl.entity.canArchive) return '';
            if ($ctrl.entityType === constants.entityType.ACCOUNT) return TOOLTIP_ARCHIVE_ACCOUNT;
            if ($ctrl.entityType === constants.entityType.CAMPAIGN) return TOOLTIP_ARCHIVE_CAMPAIGN;
            if ($ctrl.entityType === constants.entityType.AD_GROUP) return TOOLTIP_ARCHIVE_ADGROUP;
        }

        function getRestoreTooltip () {
            if (!$ctrl.entity.canRestore) return '';
            if ($ctrl.entityType === constants.entityType.ACCOUNT) return TOOLTIP_RESTORE_ACCOUNT;
            if ($ctrl.entityType === constants.entityType.CAMPAIGN) return TOOLTIP_RESTORE_CAMPAIGN;
            if ($ctrl.entityType === constants.entityType.AD_GROUP) return TOOLTIP_RESTORE_ADGROUP;
        }
    },
});
