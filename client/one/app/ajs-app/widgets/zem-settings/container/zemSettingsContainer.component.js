angular.module('one.widgets').component('zemSettingsContainer', {
    transclude: {
        settings: 'settings',
        custom: 'custom',
    },
    bindings: {
        settingsTitle: '<',
        entityType: '<',
        api: '<',
    },
    template: require('./zemSettingsContainer.component.html'),
    controller: function(
        $transclude,
        $timeout,
        $element,
        $q,
        zemPermissions,
        zemUtils,
        zemPubSubService,
        zemEntityService,
        zemNavigationService,
        zemNavigationNewService,
        $state
    ) {
        // eslint-disable-line max-len
        var STATUS_CODE_NONE = 0;
        var STATUS_CODE_IN_PROGRESS = 1;
        var STATUS_CODE_ERROR = 2;
        var STATUS_TEST_SAVE_ERROR =
            'An error occurred while saving. Please correct the marked fields and save again.';
        var HEADER_OFFSET = 78;

        var $ctrl = this;
        $ctrl.constants = constants;
        $ctrl.$container = this;
        var settingsComponents = [];

        $ctrl.entity = null;
        $ctrl.adminLink = null;
        $ctrl.errors = {};
        $ctrl.status = {
            code: STATUS_CODE_NONE,
            text: '',
        };

        $ctrl.close = close;
        $ctrl.save = save;
        $ctrl.archive = archive;
        $ctrl.restore = restore;
        $ctrl.getButtonsBarClass = getButtonsBarClass;
        $ctrl.getEntityTypeName = getEntityTypeName;
        $ctrl.getArchiveTooltip = getArchiveTooltip;
        $ctrl.getRestoreTooltip = getRestoreTooltip;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.childApi = {
            register: registerSettingsComponent,
        };

        $ctrl.$onInit = function() {
            $ctrl.api.register($ctrl.entityType, {
                save: save,
                load: load,
                scrollTo: scrollTo,
                isDirty: isDirty,
                isStateReloadNeeded: isStateReloadNeeded,
            });
        };

        function load(entity) {
            setEntity(entity);
        }

        function registerSettingsComponent(settingsComponent) {
            // Called by settings components
            //   -> validate, onSuccess, onError
            settingsComponents.push(settingsComponent);
        }

        function setEntity(entity) {
            $ctrl.origEntity = entity;
            $ctrl.entity = angular.copy(entity);
            $ctrl.adminLink = getAdminLink();
        }

        function save() {
            var validationPromises = [];
            var updateData = {settings: $ctrl.entity.settings};
            settingsComponents.forEach(function(component) {
                if (component.validate)
                    validationPromises.push(component.validate(updateData));
            });
            $q.all(validationPromises).then(function() {
                executeSave(updateData);
            });
        }

        function executeSave(updateData) {
            $ctrl.status.code = STATUS_CODE_IN_PROGRESS;
            zemEntityService
                .updateEntity($ctrl.entity.type, $ctrl.entity.id, updateData)
                .then(
                    function(entity) {
                        angular.merge($ctrl.entity, entity);
                        $ctrl.origEntity = angular.copy($ctrl.entity);
                        $ctrl.errors = {};

                        updateNavigationCache();
                        settingsComponents.forEach(function(component) {
                            if (component.onSuccess)
                                component.onSuccess($ctrl.entity);
                        });

                        close();
                    },
                    function(data) {
                        $ctrl.errors = data;
                        $ctrl.status.code = STATUS_CODE_ERROR;
                        $ctrl.status.text = STATUS_TEST_SAVE_ERROR;

                        settingsComponents.forEach(function(component) {
                            if (component.onError)
                                component.onError($ctrl.errors);
                        });
                    }
                );
        }

        function updateNavigationCache() {
            // TODO - delete (this will not be needed after removing zemNavigationService)
            if ($ctrl.entityType === constants.entityType.ACCOUNT) {
                return zemNavigationService.reloadAccount($ctrl.entity.id);
            }
            if ($ctrl.entityType === constants.entityType.CAMPAIGN) {
                return zemNavigationService.reloadCampaign($ctrl.entity.id);
            }
            if ($ctrl.entityType === constants.entityType.AD_GROUP) {
                return zemNavigationService.reloadAdGroup($ctrl.entity.id);
            }
        }

        function isDirty() {
            return !angular.equals($ctrl.origEntity, $ctrl.entity);
        }

        function isStateReloadNeeded() {
            for (var i = 0; i < settingsComponents.length; ++i) {
                var component = settingsComponents[i];
                if (
                    component.isStateReloadNeeded &&
                    component.isStateReloadNeeded()
                ) {
                    return true;
                }
            }
            return false;
        }

        function archive() {
            if (!$ctrl.entity.canArchive) return;
            $ctrl.status.code = STATUS_CODE_IN_PROGRESS;
            zemEntityService
                .executeAction(
                    constants.entityAction.ARCHIVE,
                    $ctrl.entityType,
                    $ctrl.entity.id
                )
                .then(updateNavigationCache)
                .then(function() {
                    close();
                    if ($state.includes('v2.analytics')) {
                        zemNavigationNewService.refreshState();
                    }
                });
        }

        function restore() {
            if (!$ctrl.entity.canRestore) return;
            $ctrl.status.code = STATUS_CODE_IN_PROGRESS;
            zemEntityService
                .executeAction(
                    constants.entityAction.RESTORE,
                    $ctrl.entityType,
                    $ctrl.entity.id
                )
                .then(updateNavigationCache)
                .then(load)
                .then(function() {
                    close();
                    zemNavigationNewService.refreshState();
                });
        }

        function close() {
            $ctrl.api.close();
        }

        function scrollTo(componentName) {
            var elementName = zemUtils.convertToElementName(componentName);
            var element = $('.zem-settings__body ' + elementName);
            if (element.length !== 1) return;

            $timeout(function() {
                $('.zem-settings__body').animate(
                    {
                        scrollTop: element.offset().top - HEADER_OFFSET,
                    },
                    500
                );
            });
        }

        //
        // Names & Tooltips & Styles
        //
        var TOOLTIP_ARCHIVE_ACCOUNT =
            "All of the account's campaigns have to be paused in order to archive the account."; // eslint-disable-line max-len
        var TOOLTIP_ARCHIVE_CAMPAIGN =
            "All of the campaign's ad groups have to be paused in order to archive the campaign."; // eslint-disable-line max-len
        var TOOLTIP_ARCHIVE_ADGROUP =
            'An ad group has to be paused for 3 days in order to archive it.';

        var TOOLTIP_RESTORE_ACCOUNT = '';
        var TOOLTIP_RESTORE_CAMPAIGN =
            "In order to restore a campaign, it's account must be restored first.";
        var TOOLTIP_RESTORE_ADGROUP =
            'An ad group has to be paused in order to archive it.';

        function getButtonsBarClass() {
            if ($ctrl.entityType === constants.entityType.ACCOUNT)
                return 'action-buttons-account';
            return 'action-buttons';
        }

        function getEntityTypeName() {
            if ($ctrl.entityType === constants.entityType.ACCOUNT)
                return 'account';
            if ($ctrl.entityType === constants.entityType.CAMPAIGN)
                return 'campaign';
            if ($ctrl.entityType === constants.entityType.AD_GROUP)
                return 'ad group';
        }

        function getArchiveTooltip() {
            if (!$ctrl.entity || $ctrl.entity.canArchive) return '';
            if ($ctrl.entityType === constants.entityType.ACCOUNT)
                return TOOLTIP_ARCHIVE_ACCOUNT;
            if ($ctrl.entityType === constants.entityType.CAMPAIGN)
                return TOOLTIP_ARCHIVE_CAMPAIGN;
            if ($ctrl.entityType === constants.entityType.AD_GROUP)
                return TOOLTIP_ARCHIVE_ADGROUP;
        }

        function getRestoreTooltip() {
            if (!$ctrl.entity.canRestore) return '';
            if ($ctrl.entityType === constants.entityType.ACCOUNT)
                return TOOLTIP_RESTORE_ACCOUNT;
            if ($ctrl.entityType === constants.entityType.CAMPAIGN)
                return TOOLTIP_RESTORE_CAMPAIGN;
            if ($ctrl.entityType === constants.entityType.AD_GROUP)
                return TOOLTIP_RESTORE_ADGROUP;
        }

        function getAdminLink() {
            var entity = '';
            if ($ctrl.entityType === constants.entityType.ACCOUNT)
                entity = 'account';
            if ($ctrl.entityType === constants.entityType.CAMPAIGN)
                entity = 'campaign';
            if ($ctrl.entityType === constants.entityType.AD_GROUP)
                entity = 'adgroup';

            return '/admin/dash/' + entity + '/' + $ctrl.entity.id + '/change/';
        }
    },
});
