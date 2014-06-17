/*globals oneApp*/
oneApp.controller('MainCtrl', ['$scope', '$state', function ($scope, $state) {
    $scope.adGroupId = 4;

    $scope.tabs = [
        { heading: 'Ads', route: 'adGroups.ads', active: false },
        { heading: 'Networks', route: 'adGroups.networks', active: false },
        { heading: 'Settings', route: 'adGroups.settings', active: false }
    ];

    $scope.selectTab = function (route) {
        $state.go(route, {id: $scope.adGroupId});
    };
    
    $scope.$on("$stateChangeSuccess", function() {
        $scope.tabs.forEach(function(tab) {
            tab.active = $state.is(tab.route);
        });
    });
}]);
