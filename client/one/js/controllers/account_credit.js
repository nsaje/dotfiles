/*globals oneApp*/
oneApp.controller('AccountCreditCtrl', ['$scope', '$state', '$modal', 'api', function ($scope, $state, $modal, api) {
    function error() {}
    function updateView(data, messages) {
        console.log(data)
        if (data === null) {
            error();
            return;
        } else if (data === true) {
            $scope.init();
            return;
        }
        $scope.creditTotals = data.totals;
        $scope.activeCredit = data.active;
        $scope.pastCredit = data.past;
    }
    function openModal() {
        var modalInstance = $modal.open({
            templateUrl: '/partials/account_credit_item_modal.html',
            controller: 'AccountCreditItemModalCtrl',
            windowClass: 'modal',
            scope: $scope
        });
        modalInstance.result.then(updateView);
        return modalInstance;
    }

    $scope.creditTotals = {};
    $scope.activeCredit = [];
    $scope.pastCredit = [];

    $scope.addCreditItem = function () {
        $scope.selectedCreditItemId = null;
        openModal();
    };

    $scope.editCreditItem = function (id) {
        $scope.selectedCreditItemId = id;
        openModal();
    };

    $scope.init = function () {
        if (! $scope.account) { return; }
        $scope.loadingInProgress = true;
        api.accountCredit.list($scope.account.id).then(function (data) {
            $scope.loadingInProgress = false;
            updateView(data);
        }, function (err) {
            $scope.loadingInProgress = false;
            error();
        });
    };

    $scope.init();
}]);
