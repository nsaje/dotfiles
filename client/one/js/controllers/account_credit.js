/*globals oneApp*/
oneApp.controller('AccountCreditCtrl', ['$scope', '$state', '$modal', 'api', function ($scope, $state, $modal, api) {
    function error() {}
    function refresh(updatedId) {
        $scope.updatedId = updatedId;
        $scope.init();
    }
    function updateView(data) {
        $scope.creditTotals = data.totals;
        $scope.activeCredit = data.active;
        $scope.pastCredit = data.past;
    }
    function openModal() {
        var modalInstance = $modal.open({
            templateUrl: '/partials/account_credit_item_modal.html',
            controller: 'AccountCreditItemModalCtrl',
            windowClass: 'modal',
            scope: $scope,
            size: 'wide'
        });
        modalInstance.result.then(refresh);
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
