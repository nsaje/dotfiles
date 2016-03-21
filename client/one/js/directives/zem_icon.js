/*global $,oneApp,constants*/
'use strict';

oneApp.directive('zemIcon', ['config', function (config) {
    return {
        restrict: 'E',
        scope: true,
        template: '<img class="zem-icon zem-icon-{{name}}" title="{{ title }}" ng-src="{{ config.static_url }}/one/img/{{name}}.svg" />',
        controller: ['$scope', '$attrs', function ($scope, $attrs) {
            $scope.config = config;
            $scope.title = $attrs.title;
            $scope.name = $attrs.name;
        }],
    };

}]);
