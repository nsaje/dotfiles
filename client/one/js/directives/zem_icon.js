/* global oneApp */
'use strict';

oneApp.directive('zemIcon', ['config', function (config) {
    return {
        restrict: 'E',
        scope: true,
        template: '<img class="{{ classes }}" title="{{ title }}" ng-src="{{ config.static_url }}/one/img/{{ file }}" />',
        link: function (scope, element, attrs) {
            scope.config = config;
            scope.title = attrs.title || '';
            scope.file = attrs.file;
            scope.classes = 'zem-icon';
            if (attrs.imgClass) {
                scope.classes += ' ' + attrs.imgClass;
            }
        },
    };

}]);
