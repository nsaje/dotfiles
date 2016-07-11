/* globals angular,oneApp,defaults,moment,constants */
oneApp.controller('CampaignBudgetItemModalCtrl', ['$scope', '$modalInstance', '$timeout', 'api', 'zemNavigationService', function ($scope, $modalInstance, $timeout, api, zemNavigationService) {
    $scope.today = moment().format('M/D/YYYY');
    $scope.isNew = true;
    $scope.startDatePicker = {isOpen: false};
    $scope.endDatePicker = {isOpen: false};
    $scope.isLoadingInProgress = false;
    $scope.canDelete = false;
    $scope.budgetItem = {};
    $scope.errors = {};
    $scope.minDate = null;
    $scope.maxDate = null;
    $scope.saveRequestInProgress = false;

    $scope.initStartDate = moment().toDate();
    $scope.endStartDate = null;

    $scope.getLicenseFees = function (search) {
        // use fresh instance because we modify the collection on the fly
        var fees = ['15', '20', '25'];

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

    $scope.checkCreditValues = function () {
        $timeout(function () {
            var id = $scope.budgetItem.credit.id;
            $scope.getAvailableCredit().forEach(function (obj) {
                if (obj.id !== id) { return; }

                updateBudgetInitialValues(obj);
            });
        }, 100); // to be sure that the selected id is correct

    };

    $scope.upsertBudgetItem = function () {
        $scope.saveRequestInProgress = true;
        $scope.budgetItem.id = $scope.selectedBudgetId;
        api.campaignBudget[
            $scope.isNew ? 'create' : 'save'
        ]($scope.campaign.id, $scope.budgetItem).then(function (data) {
            $scope.saved = true;
            closeModal();
            if (data.stateChanged) {
                zemNavigationService.reload();
            }
        }, function (resp) {
            $scope.errors = api.campaignBudget.convert.error(resp);
            $scope.saved = false;
        }).finally(function () {
            $scope.saveRequestInProgress = false;
        });
    };

    $scope.discardBudgetItem = function () {
        $scope.discarded = true;
        closeModal();
    };

    $scope.deleteBudgetItem = function () {
        if (!confirm('Are you sure you want to delete the budget line item?')) { return; }
        api.campaignBudget.delete($scope.campaign.id, $scope.selectedBudgetId).then(function () {
            closeModal();
        });
    };

    $scope.init = function () {
        $scope.saveRequestInProgress = false;
        $scope.isNew = $scope.selectedBudgetId === null;
        $scope.discarded = false;

        if ($scope.isNew) {
            $scope.availableCredit = $scope.getAvailableCredit(false);

            updateBudgetInitialValues($scope.availableCredit[0]);
            $scope.budgetItem.isEditable = true;
            $scope.budgetItem.credit = $scope.availableCredit[0];
        } else {
            api.campaignBudget.get(
                $scope.campaign.id,
                $scope.selectedBudgetId
            ).then(function (data) {
                $scope.budgetItem = data;

                $scope.initStartDate = moment($scope.minDate, 'MM/DD/YYYY').toDate();
                $scope.initEndDate = moment($scope.maxDate, 'MM/DD/YYYY').toDate();

                $scope.canDelete = data.state == constants.budgetLineItemStatus.PENDING;
                $scope.availableCredit = $scope.getAvailableCredit(false, data.credit.id);
                $scope.minDate = data.startDate;
                $scope.maxDate = $scope.availableCredit[0].endDate;
            });
        }
    };

    function closeModal (data) {
        $timeout(function () {
            $scope.saveRequestInProgress = false;
            $modalInstance.close(data);
        }, 1000);
    }

    function updateBudgetInitialValues (credit) {
        var creditStartDate = moment(credit.startDate, 'MM/DD/YYYY'),
            today = moment();

        $scope.minDate = credit.startDate;
        $scope.maxDate = credit.endDate;
        $scope.initEndDate = moment($scope.maxDate, 'MM/DD/YYYY').toDate();
        $scope.initStartDate = (creditStartDate > today ? creditStartDate : today).toDate();

        $scope.budgetItem.startDate = $scope.initStartDate;
        $scope.budgetItem.endDate = $scope.initEndDate;

        $scope.budgetItem.amount = parseInt(credit.available);
    }

    $scope.init();
}]);
