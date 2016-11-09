/* globals angular,defaults,moment,constants */
angular.module('one.legacy').controller('CampaignBudgetItemModalCtrl', ['$scope', '$filter', '$timeout', 'api', 'zemNavigationService', function ($scope, $filter, $timeout, api, zemNavigationService) {
    $scope.today = moment().format('MM/DD/YYYY');
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
                var creditStartDate = moment(data.startDate, 'MM/DD/YYYY').toDate(),
                    creditEndDate = moment(data.endDate, 'MM/DD/YYYY').toDate();

                $scope.budgetItem = data;
                $scope.budgetItem.startDate = creditStartDate;
                $scope.budgetItem.endDate = creditEndDate;
                $scope.budgetItem.margin = $filter('number')(
                    $scope.budgetItem.margin.replace('%', ''),
                    2
                );

                $scope.initStartDate = $scope.minDate;
                $scope.initEndDate = $scope.maxDate;

                $scope.canDelete = data.state == constants.budgetLineItemStatus.PENDING;
                $scope.availableCredit = $scope.getAvailableCredit(false, data.credit.id);
                $scope.minDate = creditStartDate;
                $scope.maxDate = moment($scope.availableCredit[0].endDate, 'MM/DD/YYYY').toDate();
            });
        }
    };

    function closeModal (data) {
        $timeout(function () {
            $scope.saveRequestInProgress = false;
            $scope.$close(data);
        }, 1000);
    }

    function updateBudgetInitialValues (credit) {
        var creditStartDate = moment(credit.startDate, 'MM/DD/YYYY').toDate(),
            creditEndDate = moment(credit.endDate, 'MM/DD/YYYY').toDate(),
            today = moment().toDate();

        $scope.minDate = creditStartDate;
        $scope.maxDate = creditEndDate;
        $scope.initEndDate = null;
        $scope.initStartDate = creditStartDate > today ? creditStartDate : today;

        $scope.budgetItem.startDate = $scope.initStartDate;
        $scope.budgetItem.endDate = $scope.initEndDate;
        $scope.budgetItem.amount = null;
    }

    $scope.init();
}]);
