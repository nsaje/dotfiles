/* globals oneApp */

oneApp.config(['$stateProvider', '$urlRouterProvider', 'config', function ($stateProvider, $urlRouterProvider, config) {
    $stateProvider
        .state('main.development', {
            url: 'development',
            template: '<div ui-view></div>',
            controller: 'DevelopmentCtrl',
        })
        .state('main.development.grid', {
            url: '/grid',
            template: '<zem-grid data-data-source="dataSource"></zem-grid>',
            controller: 'DevelopmentGridCtrl',
        });
}]);

