/*globals oneApp*/
oneApp.controller('AccountCreditCtrl', ['$scope', '$state', '$modal', '$location', 'api', 'zemMoment', function ($scope, $state, $modal, $location, api, zemMoment) {
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
            backdrop : 'static',
            size: 'wide'
        });
        modalInstance.result.then(refresh);
        return modalInstance;
    }

    $scope.creditTotals = {};
    $scope.activeCredit = [];
    $scope.pastCredit = [];

    $scope.isSelected = function (creditStartDate, creditEndDate) {
        var urlStartDate = moment($location.search().start_date).toDate(),
            urlEndDate = moment($location.search().end_date).toDate();

        creditStartDate = moment(creditStartDate, 'MM/DD/YYYY').toDate();
        creditEndDate = moment(creditEndDate, 'MM/DD/YYYY').toDate();

        return urlStartDate <= creditEndDate && urlEndDate >= creditStartDate;
    };

    $scope.$watch('dateRange', function(newValue, oldValue) {
        if (newValue.startDate.isSame(oldValue.startDate) && newValue.endDate.isSame(oldValue.endDate)) {
            return;
        }
        refresh();
    });

    $scope.addCreditItem = function () {
        $scope.selectedCreditItemId = null;
        return openModal();
    };

    $scope.editCreditItem = function (id) {
        $scope.selectedCreditItemId = id;
        return openModal();
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
