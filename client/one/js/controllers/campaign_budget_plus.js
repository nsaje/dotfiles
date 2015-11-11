/*globals oneApp*/
oneApp.controller('CampaignBudgetPlusCtrl', ['$scope', '$state', '$modal',  'api', function ($scope, $state, $modal, api) {
    function updateView(data) {
        console.log(data);

        $scope.activeBudget = data.active;
        $scope.depletedBudget = data.depleted;
        $scope.budgetTotals = data.totals;
        $scope.availableCredit = data.credits;
    }
    function openModal() {
        var modalInstance = $modal.open({
            templateUrl: '/partials/campaign_budget_item_modal.html',
            controller: 'CampaignBudgetItemModalCtrl',
            windowClass: 'modal',
            scope: $scope
        });
        modalInstance.result.then($scope.init);
        return modalInstance;
    }
    $scope.addBudgetItem = function () {
        $scope.selectedBudgetId = null;
        openModal();
    };
    $scope.editBudgetItem = function (id) {
        $scope.selectedBudgetId = id;
        openModal();
    };

    $scope.init = function () {
        if (! $scope.campaign) { return; }
        $scope.loadingInProgress = true;
        api.campaignBudgetPlus.list($scope.campaign.id).then(function (data) {
            $scope.loadingInProgress = false;
            updateView(data);
        }, function () {
            $scope.loadingInProgress = false;
        });
    };


    $scope.init();
}]);
