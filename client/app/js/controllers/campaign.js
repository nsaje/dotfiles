/*globals oneApp,$,moment*/
oneApp.controller('CampaignCtrl', ['$scope', '$state', function ($scope, $state) {
    $scope.tabs = [
        {heading: 'Agency', route: 'main.campaigns.agency', active: true, hidden: !$scope.hasPermission('dash.settings_view')}
    ];

    $scope.tabs.forEach(function(tab) {
        tab.active = $state.is(tab.route);
    });
}]);
