angular.module('one.widgets').component('zemPublisherBidModifierExportImport', {
    bindings: {
        api: '<',
    },
    bindToController: {
        grid: '=',
    },
    template: require('./zemPublisherBidModifierExportImport.component.html'),
    controller: function(
        $window,
        $uibModal,
        zemPermissions,
        zemNavigationNewService
    ) {
        var $ctrl = this;

        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isAdGroupLevel = isAdGroupLevel;
        $ctrl.execute = execute;
        $ctrl.actions = [
            {
                name: 'Export',
                value: 'export',
                execute: downloadBidModifiers,
                hasPermission: true,
            },
            {
                name: 'Import',
                value: 'import',
                execute: openImportModal,
                hasPermission: true,
            },
        ];

        function isAdGroupLevel() {
            var adGroup = zemNavigationNewService.getActiveEntityByType(
                constants.entityType.AD_GROUP
            );
            if (adGroup === undefined || adGroup === null) {
                return false;
            }
            return true;
        }

        function execute(selected) {
            for (var i = 0; i < $ctrl.actions.length; i++) {
                if ($ctrl.actions[i].value === selected) {
                    $ctrl.actions[i].execute();
                    break;
                }
            }
        }

        function download(adGroupId) {
            var url =
                '/rest/internal/adgroups/' +
                adGroupId +
                '/publishers/modifiers/download/';
            $window.open(url, '_blank');
        }

        function downloadBidModifiers() {
            var adGroupId = zemNavigationNewService.getActiveEntityByType(
                constants.entityType.AD_GROUP
            );
            if (adGroupId === null || adGroupId === undefined) {
                return;
            }
            download(adGroupId.id);
        }

        function openImportModal() {
            var adGroupId = zemNavigationNewService.getActiveEntityByType(
                constants.entityType.AD_GROUP
            );
            if (adGroupId === undefined || adGroupId === null) {
                return;
            }
            $uibModal.open({
                component: 'zemPublisherBidModifierUploadModal',
                backdrop: 'static',
                keyboard: false,
                windowClass: 'publisher-group-upload',
                resolve: {
                    adGroupId: adGroupId.id,
                },
            });
        }
    },
});
