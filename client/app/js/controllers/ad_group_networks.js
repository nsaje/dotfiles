oneApp.controller('AdGroupNetworksCtrl', ['$scope', function ($scope) {
    $scope.networks = [{
        name: 'OutBrain',
        status: 'active',
        bid_cpc: '12.3',
        daily_budget: '1000',
        cost: '3000',
        cpc: '14',
        clicks: 124,
        impressions: 1244998,
        ctr: '0.23'
    }];
    
    $scope.totals = {
        bid_cpc: '12.3',
        daily_budget: '1000',
        cost: '3000',
        cpc: '14',
        clicks: 124,
        impressions: 1244998,
        ctr: '0.23'
    };
}]);
