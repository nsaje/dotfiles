/* globals angular,oneApp,defaults,moment */
oneApp.controller('AccountCreditItemModalCtrl', ['$scope', '$modalInstance', '$timeout', 'api', function($scope, $modalInstance, $timeout, api) {
    $scope.today = moment().format('M/D/YYYY');
    $scope.isNew = true;
    $scope.startDatePicker = { isOpen: false };
    $scope.endDatePicker = { isOpen: false };
    $scope.isLoadingInProgress = false;
    $scope.canDelete = false;
    $scope.minDate = $scope.today;
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

    $scope.upsertCreditItem = function () {
        if ((!$scope.creditItem.isSigned || $scope.isNew) && $scope.isSigned) {
            $scope.creditItem.isSigned = true;
        }
        api.accountCredit[
            $scope.isNew ? 'create' : 'save'
        ]($scope.account.id, $scope.creditItem).then(closeModal, function (resp) {
            $scope.errors = api.accountCredit.convert.errors(resp);
        });
    };

    $scope.discardCreditItem = function () {
        $modalInstance.close(null);
    };
    $scope.deleteCreditItem = function () {
        if (!confirm("Are you sure you want to delete the credit line item?")) { return; }
        api.accountCredit.delete($scope.account.id, $scope.selectedCreditItemId).then(function () {
            $modalInstance.close(null);
        });
    };

    $scope.init = function () {
        var itemId = $scope.selectedCreditItemId;
        $scope.isNew = true;
        $scope.isSigned = false;
        $scope.canDelete = false;
        $scope.minDate = $scope.today;
        if (itemId !== null) {
            $scope.isLoadingInProgress = true;
            $scope.isNew = false;
            api.accountCredit.get($scope.account.id, itemId).then(function (data) {
                $scope.creditItem = data;
                $scope.isSigned = data.isSigned;
                $scope.canDelete = !data.isSigned && !data.numOfBudgets;
                $scope.minDate = data.endDate;
            }).finally(function () {
                $scope.isLoadingInProgress = false;
            });
        }
    };

    function closeModal(data) {
        $timeout(function() {
            $modalInstance.close(data || null);
        }, 1000);
    }

    $scope.init();
}]);
