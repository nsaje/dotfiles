angular.module('one.widgets').component('zemGridContainerActions', {
    template: require('./zemGridContainerActions.component.html'),
    bindings: {
        entity: '<',
        breakdown: '<',
        gridApi: '<',
    },
    controller: function (zemPermissions) {
        var $ctrl = this;
        $ctrl.constants = constants;

        $ctrl.isEntityBreakdown = isEntityBreakdown;
        $ctrl.isGridExportVisible = isGridExportVisible;
        $ctrl.isGridBulkActionsVisible = isGridBulkActionsVisible;
        $ctrl.isGridBulkPublishersActionsVisible = isGridBulkPublishersActionsVisible;
        $ctrl.isCreateEntityActionVisible = isCreateEntityActionVisible;
        $ctrl.isCreateAdGroupSourceActionVisible = isCreateAdGroupSourceActionVisible;
        $ctrl.isReportDropdownVisible = isReportDropdownVisible;
        $ctrl.canCreateNewAccount = canCreateNewAccount;

        function isEntityBreakdown () {
            return $ctrl.breakdown !== constants.breakdown.MEDIA_SOURCE
                && $ctrl.breakdown !== constants.breakdown.PUBLISHER;
        }

        function canCreateNewAccount () {
            return zemPermissions.hasPermission('zemauth.all_accounts_accounts_add_account');
        }

        function isGridBulkActionsVisible () {
            return isEntityBreakdown()
                || ($ctrl.breakdown === constants.breakdown.MEDIA_SOURCE
                    && $ctrl.entity && $ctrl.entity.type === constants.entityType.AD_GROUP);
        }

        function isGridBulkPublishersActionsVisible () {
            return $ctrl.breakdown === constants.breakdown.PUBLISHER;
        }

        function isCreateEntityActionVisible () {
            return isEntityBreakdown();
        }

        function isCreateAdGroupSourceActionVisible () {
            return $ctrl.breakdown === constants.breakdown.MEDIA_SOURCE
                && $ctrl.entity && $ctrl.entity.type === constants.entityType.AD_GROUP;
        }

        function isGridExportVisible () {
            return $ctrl.breakdown !== constants.breakdown.PUBLISHER &&
                !zemPermissions.hasPermission('zemauth.can_see_new_report_schedule');
        }

        function isReportDropdownVisible () {
            return ($ctrl.breakdown === constants.breakdown.PUBLISHER &&
                    zemPermissions.hasPermission('zemauth.can_access_publisher_reports'))
                || ($ctrl.breakdown !== constants.breakdown.PUBLISHER &&
                    zemPermissions.hasPermission('zemauth.can_see_new_report_schedule'));
        }
    },
});
