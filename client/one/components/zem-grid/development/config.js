/* globals oneApp */

oneApp.config(['$stateProvider', function ($stateProvider) {
    $stateProvider
        .state('main.development', {
            url: 'development',
            template: '<div ui-view style="padding-top:50px;"></div>',
            controller: 'DevelopmentCtrl',
        })
        .state('main.development.grid', {
            url: '/grid',
            template: '<zem-grid data-data-source="dataSource" api="gridApi"></zem-grid>',
            controller: 'DevelopmentGridCtrl',
        });
}]);

