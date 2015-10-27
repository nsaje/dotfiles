/*global $,oneApp*/
"use strict";

oneApp.directive('zemCustomTableCols', ['config', function(config) {
    return {
        restrict: 'E',
        scope: {
            columns: '=',
            categories: '=',
            localStoragePrefix: '='
        },
        templateUrl: '/partials/zem_custom_table_cols.html',
        compile: function compile(tElement, tAttrs, transclude) {
            // Prevent closing of dropdown-menu when checkbox is clicked.
            $(tElement).on('click', function(e) {
                e.stopPropagation();
            });

            return {
              pre: function preLink(scope, iElement, iAttrs, controller) {return;},
              post: function postLink(scope, iElement, iAttrs, controller) {return;}
            };
        },
        controller: ['$scope', '$element', '$attrs', 'zemCustomTableColsService', function ($scope, $element, $attrs, zemCustomTableColsService) {
            $scope.categoryColumns = [];
            $scope.hasCategories = false;

            zemCustomTableColsService.load($scope.localStoragePrefix, $scope.columns);

            $scope.filterColumns = function(col) {
                return !col.unselectable;
            };

            var updateCategories = function() {
                $scope.categoryColumns = [];
                $scope.hasCategories = false;

                for(var i = 0; i < $scope.categories.length; i++) {
                    var cat = $scope.categories[i];

                    var cols = $scope.columns.filter(function(col) {
                        return cat.fields.indexOf(col.field) !== -1 && col.shown;
                    });

                    if(cols.length > 0) {
                        $scope.categoryColumns.push({
                            'columns': cols, 
                            'name': cat.name
                        });
                        $scope.hasCategories = true;
                    }
                }
            };

            $scope.columnUpdated = function (column) {
                zemCustomTableColsService.save($scope.localStoragePrefix, $scope.columns);
            };

            $scope.$watch('categories', function (newValue, oldValue) {
                if(newValue) {
                    updateCategories();
                }
            }, true);

            $scope.$watch('columns', function (newValue, oldValue) {
                if(newValue) {
                    updateCategories();
                }
            }, true);
        }]
    };
}]);
