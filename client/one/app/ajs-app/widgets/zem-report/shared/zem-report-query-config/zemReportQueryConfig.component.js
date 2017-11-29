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
        $ctrl.selectedColumn = selectedColumn;
        $ctrl.toggleColumns = toggleColumns;
        $ctrl.showTruncatedColsList = true;

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
        $ctrl.selectedCols = [];
        $ctrl.unSelectedCols = [];

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

        function onlyUnique (value, index, self) {
            return self.indexOf(value) === index;
        }

        function toggleColumns (data) {
            var selectedColumns = data.selectedColumns.slice();
            if (data.isChecked) {
                $ctrl.selectedCols = selectedColumns;
                $ctrl.unSelectedCols = [];
            } else {
                $ctrl.unSelectedCols = selectedColumns;
                $ctrl.selectedCols = [];
            }
            $ctrl.update();
        }

        function selectedColumn (column) {
            if (column.checked) {
                $ctrl.selectedCols.push(column.name);
                var indx = $ctrl.unSelectedCols.indexOf(column.name);
                if (indx > -1) { $ctrl.unSelectedCols.splice(indx, 1); }
            } else {
                // removes columnName from selectedCols
                var index = $ctrl.selectedCols.indexOf(column.name);
                if (index > -1) { $ctrl.selectedCols.splice(index, 1); }
                $ctrl.unSelectedCols.push(column.name);
            }
            $ctrl.update();
        }

        function update () {
            var defaultFields = zemReportFieldsService.getFields(
                $ctrl.gridApi,
                $ctrl.breakdown,
                $ctrl.config.includeIds
            );
            var selectedFields = $ctrl.selectedCols;
            var unSelectedFields = $ctrl.unSelectedCols;

            var mergedFields = defaultFields.filter(function (field) {
                return unSelectedFields.indexOf(field) === -1;
            }).concat(selectedFields).filter(onlyUnique);

            $ctrl.config.selectedFields = mergedFields;
            $ctrl.showAllSelectedFields();

            if ($ctrl.shownSelectedFields.length > SHORTLIST_LIMIT && $ctrl.showTruncatedColsList) {
                // user sees "..." only once. If the user interacts with column
                // selection component we display all columns
                $ctrl.showTruncatedColsList = false;
                $ctrl.shownSelectedFields = $ctrl.config.selectedFields.slice(0, SHORTLIST_LIMIT);
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
