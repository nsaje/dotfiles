/* globals angular,oneApp,defaults,moment */
oneApp.controller('AccountCreditItemModalCtrl', ['$scope', '$modalInstance', '$timeout', 'api', function($scope, $modalInstance, $timeout, api) {
    $scope.today = moment().format('M/D/YYYY');
    $scope.isNew = true;
    $scope.startDatePicker = { isOpen: false };
    $scope.endDatePicker = { isOpen: false };
    $scope.isLoadingInProgress = false;
    $scope.canDelete = false;
    $scope.creditItem = {};
    $scope.errors = {};

    $scope.getLicenseFees = function(search) {
        // use fresh instance because we modify the collection on the fly
        var fees = ['15%', '20%', '25%'];

        // adds the searched for value to the array
        if (search && fees.indexOf(search) === -1) {
            fees.unshift(search);
        }

        return fees;
    };

    

    $scope.openDatePicker = function (type) {
        if (type === 'startDate') {
            $scope.startDatePicker.isOpen = true;
        } else if (type === 'endDate') {
            $scope.endDatePicker.isOpen = true;
        }
    };

    $scope.saveCreditItem = function () {
        api.accountCredit[
            $scope.isNew ? 'create' : 'save'
        ]($scope.account.id, $scope.creditItem).then(closeModal, function (resp) {
            $scope.errors = {
                startDate: resp.data.data.errors.start_date,
                endDate: resp.data.data.errors.end_date,
                amount: resp.data.data.errors.amount,
                licenseFee: resp.data.data.errors.license_fee,
                comment: resp.data.data.errors.comment
            };
        });
    };

    $scope.discardCreditItem = function () {
        $modalInstance.close(null);
    };
    $scope.deleteCreditItem = function () {
        api.accountCredit.delete($scope.account.id, $scope.selectedCreditItemId).then(function () {
            $modalInstance.close(true);
        });
    };

    $scope.init = function () {
        var itemId = $scope.selectedCreditItemId;
        $scope.isNew = true;
        $scope.canDelete = false;
        if (itemId !== null) {
            $scope.isLoadingInProgress = true;
            $scope.isNew = false;
            api.accountCredit.get($scope.account.id, itemId).then(function (data) {
                $scope.creditItem = data;
                console.log(data)
                $scope.canDelete = !data.isSigned && !data.numOfBudgets;
            }).finally(function () {
                $scope.isLoadingInProgress = false;
            });
        }
    };

    function closeModal(data) {
        $timeout(function() {
            $modalInstance.close(data.id ? null : data);
        }, 1000);
    }

    $scope.init();
}]);
