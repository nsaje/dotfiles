/*globals oneApp*/
oneApp.controller('MainCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.tabs = [
        {heading: 'Ads', route: 'adGroups.ads', active: true},
        {heading: 'Networks', route: 'adGroups.networks', active: false},
        {heading: 'Settings', route: 'adGroups.settings', active: false}
    ];
    
    $scope.$on("$stateChangeSuccess", function() {
        $scope.tabs.forEach(function(tab) {
            tab.active = $state.is(tab.route);
        });
    });

    api.navData.list().then(function(data) {
        $scope.accounts = data;
    });
}]);
