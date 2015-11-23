/* globals angular,oneApp,defaults,moment */
oneApp.controller('AccountCreditItemModalCtrl', ['$scope', '$modalInstance', '$timeout', '$window', 'api', function($scope, $modalInstance, $timeout, $window, api) {
    $scope.today = moment().format('M/D/YYYY');
    $scope.isNew = true;
    $scope.startDatePicker = { isOpen: false };
    $scope.endDatePicker = { isOpen: false };
    $scope.isLoadingInProgress = false;
    $scope.saveRequestInProgress = false;
    $scope.canDelete = false;
    $scope.minDate = $scope.today;
    $scope.creditItem = {
        startDate: moment().format('MM/DD/YYYY')
    };
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

    $scope.openStartDatePicker = function () {
        $scope.startDatePicker.isOpen = true;
    };
    $scope.openEndDatePicker = function () {
        $scope.endDatePicker.isOpen = true;
    };

    $scope.upsertCreditItem = function () {
        $scope.saveRequestInProgress = true;
        api.accountCredit[
            $scope.isNew ? 'create' : 'save'
        ]($scope.account.id, $scope.creditItem).then(function () {
            $scope.saved = true;
            closeModal();
        }, function (resp) {
            $scope.errors = api.accountCredit.convert.errors(resp);
        }).finally(function () {
            $scope.saveRequestInProgress = false;
        });
    };

    $scope.discardCreditItem = function () {
        $scope.discarded = true;
        closeModal();
    };
    $scope.deleteCreditItem = function () {
        if (!$window.confirm("Are you sure you want to delete the credit line item?")) { return; }
        api.accountCredit.delete($scope.account.id, $scope.selectedCreditItemId).then(function () {
            $modalInstance.close(null);
        });
    };

    $scope.init = function () {
        var itemId = $scope.selectedCreditItemId;
        $scope.isNew = true;
        $scope.wasSigned = false;
        $scope.canDelete = false;
        $scope.minDate = $scope.today;
        $scope.initStartDate = moment().toDate();
        $scope.discarded = false;
        
        if (itemId !== null) {
            $scope.isLoadingInProgress = true;
            $scope.isNew = false;
            api.accountCredit.get($scope.account.id, itemId).then(function (data) {
                $scope.creditItem = data;
                $scope.wasSigned = data.isSigned;
                $scope.canDelete = !data.isSigned && !data.numOfBudgets;
                $scope.minDate = data.endDate;
            }).finally(function () {
                $scope.isLoadingInProgress = false;
            });
        }
    };

    function closeModal(data) {
        $timeout(function() {
            $scope.saveRequestInProgress = false;
            $modalInstance.close(data);
        }, 1000);
    }

    $scope.init();
}]);
