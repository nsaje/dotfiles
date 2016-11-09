/* globals angular */

angular.module('one.legacy').config(function ($stateProvider) {
    $stateProvider
        .state('main.development', {
            url: 'development',
            template: '<div ui-view style="padding-top:50px;"></div>',
            controller: 'DevelopmentCtrl',
        })
        .state('main.development.grid', {
            url: '/grid',
            template: '' +
                '<zem-grid-action-bar api="grid.api"></zem-grid-action-bar>' +
                '<zem-grid data-data-source="grid.dataSource" api="grid.api" options="grid.options"></zem-grid>',
            controller: 'DevelopmentGridCtrl',
        });
});

