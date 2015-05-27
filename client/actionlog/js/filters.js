/*global $,oneApp*/
"use strict";

actionLogApp.directive('zemActionLogFilter', function() {
    return {
        restrict: 'E',
        scope: {
            field: '=field',
            filters: '=filters',
        },
        template:
            '<div class="btn-group actionlog-filter" dropdown>' +
                '<button type="button" class="btn btn-default btn-xs dropdown-toggle" dropdown-toggle>' +
                    '{{filters.selected[field][1]}} <span class="caret"></span>' +
                '</button>' +
                '<ul class="dropdown-menu filter-dropdown" role="menu" dropdown-menu>' +
                    '<li ng-repeat="choice in filters.items[field]">' +
                        '<a href="" ng-click="filters.update(field, choice)">{{choice[1]}}</a>' +
                    '</li>' +
                '</ul>' +
            '</div>'
    };
});

