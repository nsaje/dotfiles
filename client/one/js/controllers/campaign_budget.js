/*globals oneApp,constants,options,moment*/
oneApp.controller('CampaignBudgetCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.total = 0;
    $scope.spend = 0;
    $scope.available = 0;
    $scope.errors = {};
    $scope.history = [];
    $scope.latestId = null;
    $scope.allocate = 0;
    $scope.revoke = 0;
    $scope.comment = '';
    $scope.requestInProgress = false;

    $scope.getBudget = function() {
        $scope.requestInProgress = true;
        
        api.campaignBudget.get($state.params.id).then(
            function (data) {
                $scope.total = data.total;
                $scope.spend = data.spend;
                $scope.available = data.available;
                $scope.history = data.history;
                $scope.latestId = data.latest_id;
            },
            function (data) {
                // error
                return
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    $scope.saveBudget = function() {
        $scope.requestInProgress = true;

        api.campaignBudget.save($state.params.id, {
            allocate: $scope.allocate, 
            revoke: $scope.revoke, 
            comment: $scope.comment, 
            latest_id: $scope.latestId
        }).then(
            function (data) {
                $scope.total = data.total;
                $scope.spend = data.spend;
                $scope.available = data.available;
                $scope.history = data.history;
                $scope.latestId = data.latest_id;
                $scope.allocate = 0;
                $scope.revoke = 0;
                $scope.comment = '';
                $scope.errors = 0;
            },
            function (data) {
                // error
                $scope.errors = data.data.errors;
                console.log(JSON.stringify($scope.errors));
                console.log($scope.errors);
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    $scope.getBudget();

}]);