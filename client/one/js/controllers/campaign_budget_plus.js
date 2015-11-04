/*globals oneApp*/
oneApp.controller('CampaignBudgetPlusCtrl', ['$scope', '$state', '$modal',  'api', function ($scope, $state, $modal, api) {
    function openModal() {
        var modalInstance = $modal.open({
            templateUrl: '/partials/campaign_budget_item_modal.html',
            controller: 'CampaignBudgetItemModalCtrl',
            windowClass: 'modal',
            scope: $scope
        });
        modalInstance.result.then(function () {
            alert('dobim nekaj nazaj');
        });
        return modalInstance;
    }
    $scope.addBudgetItem = function () {
        openModal();
    };
}]);
