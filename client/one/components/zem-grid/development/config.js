/* globals oneApp,angular */

oneApp.config(['$stateProvider', '$urlRouterProvider', 'config', function ($stateProvider, $urlRouterProvider, config) {
    $stateProvider
        .state('main.development', {
            url: 'development',
            template: '<div ui-view></div>',
        })
        .state('main.development.grid', {
            url: '/grid',
            template: '<zem-grid data-data-source="dataSource"></zem-grid>',
            controller: 'DevelopmentGridCtrl',
        })
        .state('main.development.grid-legacy', {
            url: '/grid-legacy',
            template: '<zem-grid data-data-source="dataSource"></zem-grid>',
            controller: 'DevelopmentGridCachedCtrl',
        });
}]);

