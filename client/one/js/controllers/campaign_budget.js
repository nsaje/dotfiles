/*globals oneApp,constants,options,moment*/
oneApp.controller('CampaignBudgetCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.total = 0;
    $scope.spend = 0;
    $scope.available = 0;
    $scope.errors = {};
    $scope.history = [];
    $scope.amount = 0;
    $scope.action = null;
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
            amount: $scope.amount, 
            action: $scope.action, 
            comment: $scope.comment
        }).then(
            function (data) {
                $scope.total = data.total;
                $scope.spend = data.spend;
                $scope.available = data.available;
                $scope.history = data.history;
                $scope.amount = 0;
                $scope.action = null;
                $scope.comment = '';
                $scope.errors = 0;
            },
            function (data) {
                // error
                $scope.errors = data.data.errors;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    $scope.allocateBudget = function() {
        $scope.action = 'allocate';
        $scope.saveBudget();
    };

    $scope.revokeBudget = function() {
        $scope.action = 'revoke';
        $scope.saveBudget();
    }

    $scope.getBudget();

}]);
