/*globals oneApp*/
oneApp.controller('MainCtrl', ['$scope', '$state', function ($scope, $state) {
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
}]);
