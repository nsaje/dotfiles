/*globals oneApp,constants,options,moment*/
oneApp.controller('CampaignBudgetCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.total = 10000;
    $scope.spend = 8000;
    $scope.available = 2000;
    $scope.history = [];
    // $scope.history = [
    //     {
    //         datetime: '2014-09-26T16:16:08.545317',
    //         user: 'lori@pofa.be',
    //         allocate: 10000,
    //         revoke: 0,
    //         total: 30000,
    //         comment: 'Helo bello'
    //     },
    //     {
    //         datetime: '2014-09-26T16:16:08.545317',
    //         user: 'super@user.com',
    //         allocate: 0,
    //         revoke: 3000,
    //         total: 20000,
    //         comment: 'Bunica bate toba'
    //     }
    // ];
    $scope.latestId = null;
    $scope.allocate = 0;
    $scope.revoke = 0;
    $scope.comment = '';
    $scope.requestInProgress = false;

    $scope.getBudget = function() {
        $scope.requestInProgress = true;
        console.log('getBudget()')
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
        console.log('allocate $' + $scope.allocate);
        console.log('revoke $' + $scope.revoke);
        console.log('comment: ' + $scope.comment);

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
            },
            function (data) {
                // error
                console.log('ERROR');
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    $scope.getBudget();

}]);