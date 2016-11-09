/* globals angular,defaults,moment */
angular.module('one.legacy').controller('AccountCreditItemModalCtrl', function ($scope, $timeout, $window, $filter, api) {
    var currentMoment = moment();
    $scope.today = currentMoment.format('M/D/YYYY');
    $scope.isNew = true;
    $scope.startDatePicker = {isOpen: false};
    $scope.endDatePicker = {isOpen: false};
    $scope.startDatePickerOptions = {minDate: currentMoment.toDate()};
    $scope.endDatePickerOptions = {minDate: currentMoment.toDate()};
    $scope.isLoadingInProgress = false;
    $scope.saveRequestInProgress = false;
    $scope.canDelete = false;
    $scope.creditItem = {
        startDate: currentMoment.toDate(),
    };
    $scope.errors = {};

    $scope.getLicenseFees = function (search, additional) {
        // use fresh instance because we modify the collection on the fly
        var fees = ['15.00', '20.00', '25.00'];
        if (additional !== undefined) {
            if (fees.indexOf(additional) === -1) {
                fees.push(additional);
            }
            fees.sort();
        }
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

        cleanInput($scope.creditItem);
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
        if (!$window.confirm('Are you sure you want to delete the credit line item?')) { return; }
        api.accountCredit.delete($scope.account.id, $scope.selectedCreditItemId).then(function () {
            $scope.$close(null);
        });
    };

    $scope.init = function () {
        var itemId = $scope.selectedCreditItemId;
        $scope.isNew = true;
        $scope.wasSigned = false;
        $scope.canDelete = false;
        $scope.discarded = false;

        if (itemId !== null) {
            $scope.isLoadingInProgress = true;
            $scope.isNew = false;
            api.accountCredit.get($scope.account.id, itemId).then(function (data) {
                $scope.creditItem = data;
                $scope.creditItem.startDate = moment(data.startDate, 'M/D/YYYY').toDate();
                $scope.creditItem.endDate = moment(data.endDate, 'M/D/YYYY').toDate();
                $scope.wasSigned = data.isSigned;
                $scope.canDelete = !data.isSigned && !data.numOfBudgets;
                $scope.endDatePickerOptions = {minDate: moment(data.endDate, 'M/D/YYYY').toDate()};
                $scope.creditItem.licenseFee = $filter('number')(
                    $scope.creditItem.licenseFee.replace('%', ''),
                    2
                );
            }).finally(function () {
                $scope.isLoadingInProgress = false;
            });
        }
    };

    function closeModal (data) {
        $timeout(function () {
            $scope.saveRequestInProgress = false;
            $scope.$close(data);
        }, 1000);
    }

    function cleanInput (data) {
        if (data.licenseFee) {
            data.licenseFee = $filter('number')(
                data.licenseFee,
                2
            );
        }
    }

    $scope.init();
});
