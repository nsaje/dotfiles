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
            backdrop : 'static',
            scope: $scope,
            size: 'wide'
        });
        modalInstance.result.then(refresh);
        return modalInstance;
    }

    $scope.getAvailableCredit = function (all, include) {
        return all ? availableCredit : availableCredit.filter(function (obj) {
            return include && obj.id === include || !include && obj.isAvailable;
        });
    };
    
    $scope.addBudgetItem = function () {
        $scope.selectedBudgetId = null;
        return openModal();
    };
    $scope.editBudgetItem = function (id) {
        $scope.selectedBudgetId = id;
        return openModal();
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
