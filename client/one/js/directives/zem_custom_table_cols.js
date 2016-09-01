/*global $,oneApp,constants*/
'use strict';

oneApp.directive('zemCustomTableCols', ['config', function (config) {
    return {
        restrict: 'E',
        scope: {
            columns: '=',
            categories: '=',
            localStoragePrefix: '='
        },
        templateUrl: '/partials/zem_custom_table_cols.html',
        link: function postLink (scope, element) {
            // Prevent closing of dropdown-menu when clicking inside it.
            var dropdownMenu = element.find('[uib-dropdown-menu]');
            dropdownMenu.on('click', function (event) {
                event.stopPropagation();
            });
            scope.$on('$destroy', function () {
                dropdownMenu.off('click');
            });
        },
        controller: ['$scope', '$element', '$attrs', 'zemCustomTableColsService', function ($scope, $element, $attrs, zemCustomTableColsService) {
            $scope.categoryColumns = [];
            $scope.hasCategories = false;
            $scope.constants = constants;

            zemCustomTableColsService.load($scope.localStoragePrefix, $scope.columns);

            $scope.filterColumns = function (col) {
                return !col.unselectable;
            };

            var updateCategories = function () {
                var categoryColumns = [],
                    hasCategories = false;

                for (var i = 0; i < $scope.categories.length; i++) {
                    var cat = $scope.categories[i];

                    var cols = $scope.columns.filter(function (col) {
                        return cat.fields.indexOf(col.field) !== -1 && col.shown;
                    });

                    if (cols.length > 0) {
                        categoryColumns.push({
                            'columns': cols,
                            'name': cat.name
                        });
                        hasCategories = true;
                    }
                }
                $scope.categoryColumns = categoryColumns;
                $scope.hasCategories = hasCategories;
            };

            $scope.columnUpdated = function (column) {
                zemCustomTableColsService.save($scope.localStoragePrefix, $scope.columns);
            };

            $scope.$watch('categories', function (newValue, oldValue) {
                if (newValue) {
                    updateCategories();
                    zemCustomTableColsService.load($scope.localStoragePrefix, $scope.columns);
                }
            }, true);

            $scope.$watch('columns', function (newValue, oldValue) {
                if (newValue) {
                    updateCategories();
                    zemCustomTableColsService.load($scope.localStoragePrefix, $scope.columns);
                }
            }, true);
        }]
    };
}]);
