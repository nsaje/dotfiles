require('./zemColumnSelector.component.less');

angular.module('one.widgets').component('zemColumnSelector', {
    bindings: {
        categories: '<',
        onColumnToggled: '&',
        onColumnsToggled: '&',
        onAllColumnsToggled: '&',
    },
    template: require('./zemColumnSelector.component.html'),
    controller: function(zemAuthStore) {
        var MSG_DISABLED_COLUMN =
            'Column is available when corresponding breakdown is visible.';

        var $ctrl = this;

        $ctrl.hasPermission = zemAuthStore.hasPermission.bind(zemAuthStore);
        $ctrl.searchQuery = '';
        $ctrl.getTooltip = getTooltip;
        $ctrl.onSearch = onSearch;

        $ctrl.$onChanges = function(changes) {
            if (changes.categories) {
                onSearch($ctrl.searchQuery);
            }
        };

        function onSearch(q) {
            $ctrl.searchQuery = q.toLowerCase();
            $ctrl.filteredCategories = getFilteredCategories(
                $ctrl.categories,
                $ctrl.searchQuery
            );
        }

        function getFilteredCategories(categories, searchQuery) {
            categories = angular.copy(categories);
            categories.forEach(function(category) {
                category.columns = getFilteredColumns(category, searchQuery);
                category.subcategories = getFilteredSubcategories(
                    category.subcategories,
                    searchQuery
                );
            });
            return categories.filter(removeEmptyCategories);
        }

        function getFilteredColumns(category, searchQuery) {
            return category.columns.filter(function(column) {
                var field = column.data.name.toLowerCase();
                return field.indexOf(searchQuery) !== -1;
            });
        }

        function getFilteredSubcategories(subcategories, searchQuery) {
            return (subcategories || []).filter(function(subcategory) {
                var field = subcategory.name.toLowerCase();
                return field.indexOf(searchQuery) !== -1;
            });
        }

        function removeEmptyCategories(category) {
            return (
                category.columns.length > 0 ||
                (category.subcategories || []).some(function(subCategory) {
                    return removeEmptyCategories(subCategory);
                })
            );
        }

        function getTooltip(column) {
            if (column.disabled) {
                return MSG_DISABLED_COLUMN;
            }
            return null;
        }
    },
});
