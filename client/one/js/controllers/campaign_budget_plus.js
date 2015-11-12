/*globals oneApp*/
oneApp.controller('CampaignBudgetPlusCtrl', ['$scope', '$state', '$modal',  'api', function ($scope, $state, $modal, api) {
    var availableCredit = [];
    function updateView(data) {
        $scope.activeBudget = data.active;
        $scope.depletedBudget = data.depleted;
        $scope.budgetTotals = data.totals;
        availableCredit = data.credits;
    }
    function refresh(updatedId) {
        $scope.updatedId = updatedId;
        $scope.init();
    }
    function openModal() {
        var modalInstance = $modal.open({
            templateUrl: '/partials/campaign_budget_item_modal.html',
            controller: 'CampaignBudgetItemModalCtrl',
            windowClass: 'modal',
            scope: $scope
        });
        modalInstance.result.then(refresh);
        return modalInstance;
    }

    $scope.getAvailableCredit = function (all, include) {
        return all ? availableCredit : availableCredit.filter(function (obj) {
            return obj.isAvailable || obj.id === include;
        });
    };
    
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
