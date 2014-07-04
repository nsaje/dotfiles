/*global $,oneApp*/
"use strict";

oneApp.directive('zemCustomTableCols', function(config) {
    return {
        restrict: 'E',
        scope: {
            columns: '='
        },
        template: '<span class="dropdown custom-cols"><a href class="btn btn-default dropdown-toggle" title="Show/hide columns">...</a><ul class="dropdown-menu dropdown-menu-right"><li ng-repeat="col in columns"><div class="checkbox"><label><input type="checkbox" ng-model="col.checked">{{ col.name }}</label></div></li></ul></span>',
        compile: function compile(tElement, tAttrs, transclude) {
            // Prevent closing of dropdown-menu when checkbox is clicked.
            $(tElement).on('click', function(e) {
                e.stopPropagation();
            });

            return {
              pre: function preLink(scope, iElement, iAttrs, controller) {return;},
              post: function postLink(scope, iElement, iAttrs, controller) {return;}
            };
        }
    };
});
