require('./zemColumnSelector.component.less');

angular.module('one.widgets').component('zemColumnSelector', {
    bindings: {
        bareBoneCategories: '=',
        filteredBareCategories: '=',
        onSelectColumn: '&',
        onToggleColumns: '&',
    },
    template: require('./zemColumnSelector.component.html'),
    controller: function () {
        var MSG_DISABLED_COLUMN = 'Column is available when coresponding breakdown is visible.';

        var $ctrl = this;

        $ctrl.searchQuery = '';
        $ctrl.getTooltip = getTooltip;
        $ctrl.onSearch = onSearch;


        $ctrl.$onInit = function () {
            $ctrl.filteredBareCategories = cloneObjects($ctrl.bareBoneCategories);
        };

        function getTooltip (column) {
            if (column.disabled) {
                return MSG_DISABLED_COLUMN;
            }
            return null;
        }

        function onSearch (q) {
            $ctrl.searchQuery = q.toLowerCase();
            $ctrl.filteredBareCategories = cloneObjects($ctrl.bareBoneCategories);

            $ctrl.filteredBareCategories.forEach(function (bareBoneCategory) {
                bareBoneCategory.columns = bareBoneCategory.columns.filter(function (column) {
                    var field = column.name.toLowerCase();
                    return field.indexOf($ctrl.searchQuery) !== -1;
                });
            });

            // filters out categories without columns
            $ctrl.filteredBareCategories = $ctrl.filteredBareCategories.filter(function (bareBoneCategory) {
                return bareBoneCategory.columns.length > 0;
            });
        }

        function cloneObjects (arr) {
            return arr.map(function (bareBoneCategory) {
                return angular.extend({}, bareBoneCategory);
            });
        }
    }
});
