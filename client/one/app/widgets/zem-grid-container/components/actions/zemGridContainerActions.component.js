angular.module('one.widgets').component('zemGridContainerActions', {
    templateUrl: '/app/widgets/zem-grid-container/components/actions/zemGridContainerActions.component.html',
    bindings: {
        entity: '<',
        breakdown: '<',
        gridApi: '<',
    },
    controller: function () {
        var $ctrl = this;
        $ctrl.constants = constants;

        $ctrl.isEntityBreakdown = isEntityBreakdown;
        $ctrl.isGridExportVisible = isGridExportVisible;
        $ctrl.isGridBulkActionsVisible = isGridBulkActionsVisible;
        $ctrl.isGridBulkPublishersActionsVisible = isGridBulkPublishersActionsVisible;
        $ctrl.isCreateEntityActionVisible = isCreateEntityActionVisible;
        $ctrl.isCreateAdGroupSourceActionVisible = isCreateAdGroupSourceActionVisible;

        function isEntityBreakdown () {
            return $ctrl.breakdown !== constants.breakdown.MEDIA_SOURCE
                && $ctrl.breakdown !== constants.breakdown.PUBLISHER;
        }

        function isGridBulkActionsVisible () {
            return isEntityBreakdown()
                || ($ctrl.breakdown === constants.breakdown.MEDIA_SOURCE
                    && $ctrl.entity.level === constants.level.AD_GROUPS);
        }

        function isGridBulkPublishersActionsVisible () {
            return $ctrl.breakdown === constants.breakdown.PUBLISHER
                && $ctrl.entity.level === constants.level.AD_GROUPS;
        }

        function isCreateEntityActionVisible () {
            return isEntityBreakdown();
        }

        function isCreateAdGroupSourceActionVisible () {
            return $ctrl.breakdown === constants.breakdown.MEDIA_SOURCE
                && $ctrl.entity.level === constants.level.AD_GROUPS;

        }

        function isGridExportVisible () {
            return $ctrl.breakdown !== constants.breakdown.PUBLISHER;
        }
    },
});
