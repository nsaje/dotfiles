require('./zemReportQueryConfig.component.less');

angular.module('one.widgets').component('zemReportQueryConfig', {
    bindings: {
        gridApi: '<',
        disabled: '<',
        config: '=',
    },
    template: require('./zemReportQueryConfig.component.html'),
    controller: function (zemFilterSelectorService, zemReportBreakdownService, zemReportFieldsService, zemPermissions) {
        var $ctrl = this;

        var NR_SHORTLIST_ITEMS = 9;
        var SHORTLIST_LIMIT = 15;

        //
        // Public API
        //
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.showAllSelectedFields = showAllSelectedFields;
        $ctrl.showAllAppliedFilters = showAllAppliedFilters;
        $ctrl.addBreakdown = addBreakdown;
        $ctrl.removeBreakdown = removeBreakdown;
        $ctrl.update = update;

        // template variables
        $ctrl.config = {
            includeTotals: false,
            includeIds: false,
            includeItemsWithNoSpend: false,
            selectedFields: [],
        };
        $ctrl.showIncludeItemsWithNoSpend = true;
        $ctrl.shownSelectedFields = [];
        $ctrl.appliedFilterConditions = [];
        $ctrl.view = '';
        $ctrl.breakdown = [];
        $ctrl.availableBreakdowns = {};

        $ctrl.$onInit = function () {
            $ctrl.appliedFilterConditions = zemFilterSelectorService.getAppliedConditions();
            if ($ctrl.appliedFilterConditions.length > SHORTLIST_LIMIT) {
                $ctrl.shownAppliedFilterConditions = $ctrl.appliedFilterConditions.slice(0, NR_SHORTLIST_ITEMS);
            } else {
                $ctrl.showAllAppliedFilters();
            }

            $ctrl.breakdown = angular.copy($ctrl.gridApi.getBreakdown());

            $ctrl.view = $ctrl.breakdown[0].report_query;
            if ($ctrl.view === 'Publisher') {
                $ctrl.showIncludeItemsWithNoSpend = false;
            }

            update();
        };

        function addBreakdown (breakdown) {
            $ctrl.breakdown.push(breakdown);
            update();
        }

        function removeBreakdown (breakdown) {
            $ctrl.breakdown.splice($ctrl.breakdown.indexOf(breakdown), 1);
            update();
        }

        function update () {
            $ctrl.config.selectedFields = zemReportFieldsService.getFields(
                $ctrl.gridApi,
                $ctrl.breakdown,
                $ctrl.config.includeIds
            );
            if ($ctrl.shownSelectedFields.length <= NR_SHORTLIST_ITEMS &&
                    $ctrl.config.selectedFields.length > SHORTLIST_LIMIT) {
                $ctrl.shownSelectedFields = $ctrl.config.selectedFields.slice(0, NR_SHORTLIST_ITEMS);
            } else {
                $ctrl.showAllSelectedFields();
            }

            $ctrl.shownBreakdown = $ctrl.breakdown.slice(1, $ctrl.breakdown.length);

            $ctrl.availableBreakdowns = zemReportBreakdownService.getAvailableBreakdowns(
                $ctrl.breakdown,
                $ctrl.gridApi.getMetaData()
            );
        }

        function showAllSelectedFields () {
            $ctrl.shownSelectedFields = $ctrl.config.selectedFields;
        }

        function showAllAppliedFilters () {
            $ctrl.shownAppliedFilterConditions = $ctrl.appliedFilterConditions;
        }
    },
});
