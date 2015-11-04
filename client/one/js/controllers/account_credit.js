/*globals oneApp*/
oneApp.controller('AccountCreditCtrl', ['$scope', '$state', '$modal', 'api', function ($scope, $state, $modal, api) {
    function openModal() {
        var modalInstance = $modal.open({
            templateUrl: '/partials/account_credit_item_modal.html',
            controller: 'AccountCreditItemModalCtrl',
            windowClass: 'modal',
            scope: $scope
        });
        modalInstance.result.then(function () {
            alert('dobim nekaj nazaj');
        });
        return modalInstance;
    }
    $scope.addCreditItem = function () {
        openModal();
    };
}]);
