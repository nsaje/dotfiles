/*global $,oneApp*/
"use strict";

oneApp.directive('zemCustomTableCols', ['config', function(config) {
    return {
        restrict: 'E',
        scope: {
            columns: '=',
            categories: '=',
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
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
            $scope.categoryColumns = [];
            $scope.hasCategories = false;

            $scope.$watch('categories', function (newValue, oldValue) {
                if(newValue) {
                    $scope.categoryColumns = [];
                    $scope.hasCategories = false;

                    for(var i = 0; i < $scope.categories.length; i++) {
                        var cat = $scope.categories[i];

                        var cols = $scope.columns.filter(function(col) {
                            return cat.fields.indexOf(col.field) != -1 && col.shown;
                        });

                        if(cols.length > 0) {
                            $scope.categoryColumns.push({
                                'columns': cols, 
                                'name': cat.name
                            });
                            $scope.hasCategories = true;
                        }
                    }
                }
            }, true);
        }]
    };
}]);
