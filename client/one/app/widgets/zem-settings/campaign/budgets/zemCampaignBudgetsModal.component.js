/* globals angular,moment,constants */
angular.module('one.widgets').component('zemCampaignBudgetsModal', {
    templateUrl: '/app/widgets/zem-settings/campaign/budgets/zemCampaignBudgetsModal.component.html',
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    controller: function ($filter, $timeout, zemCampaignBudgetsEndpoint, zemNavigationService, zemPermissions) {
        var $ctrl = this;

        $ctrl.campaign = $ctrl.resolve.campaign;
        $ctrl.selectedBudgetId = $ctrl.resolve.selectedBudgetId;
        $ctrl.credits = $ctrl.resolve.credits;

        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.today = moment().format('MM/DD/YYYY');
        $ctrl.isNew = true;
        $ctrl.startDatePicker = {isOpen: false};
        $ctrl.endDatePicker = {isOpen: false};
        $ctrl.isLoadingInProgress = false;
        $ctrl.canDelete = false;
        $ctrl.budgetItem = {};
        $ctrl.errors = {};
        $ctrl.minDate = null;
        $ctrl.maxDate = null;
        $ctrl.saveRequestInProgress = false;

        $ctrl.initStartDate = moment().toDate();
        $ctrl.endStartDate = null;

        $ctrl.getLicenseFees = function (search) {
            // use fresh instance because we modify the collection on the fly
            var fees = ['15', '20', '25'];

            // adds the searched for value to the array
            if (search && fees.indexOf(search) === -1) {
                fees.unshift(search);
            }

            return fees;
        };

        $ctrl.openStartDatePicker = function () {
            $ctrl.startDatePicker.isOpen = true;
        };
        $ctrl.openEndDatePicker = function () {
            $ctrl.endDatePicker.isOpen = true;
        };

        $ctrl.checkCreditValues = function () {
            $timeout(function () {
                var id = $ctrl.budgetItem.credit.id;
                getAvailableCredit().forEach(function (obj) {
                    if (obj.id !== id) {
                        return;
                    }

                    updateBudgetInitialValues(obj);
                });
            }, 100); // to be sure that the selected id is correct

        };

        $ctrl.upsertBudgetItem = function () {
            $ctrl.saveRequestInProgress = true;
            $ctrl.budgetItem.id = $ctrl.selectedBudgetId;
            var endpoint = $ctrl.isNew ? zemCampaignBudgetsEndpoint.create : zemCampaignBudgetsEndpoint.save;
            endpoint($ctrl.campaign.id, $ctrl.budgetItem).then(function (data) {
                $ctrl.saved = true;
                closeModal();
                if (data.stateChanged) {
                    zemNavigationService.reload();
                }
            }, function (errors) {
                $ctrl.errors = errors;
                $ctrl.saved = false;
            }).finally(function () {
                $ctrl.saveRequestInProgress = false;
            });
        };

        $ctrl.discardBudgetItem = function () {
            $ctrl.discarded = true;
            closeModal();
        };

        $ctrl.deleteBudgetItem = function () {
            if (!confirm('Are you sure you want to delete the budget line item?')) {
                return;
            }
            zemCampaignBudgetsEndpoint.delete($ctrl.campaign.id, $ctrl.selectedBudgetId).then(function () {
                closeModal();
            });
        };

        $ctrl.$onInit = function () {
            $ctrl.saveRequestInProgress = false;
            $ctrl.isNew = $ctrl.selectedBudgetId === null;
            $ctrl.discarded = false;

            if ($ctrl.isNew) {
                $ctrl.availableCredit = getAvailableCredit(false);

                updateBudgetInitialValues($ctrl.availableCredit[0]);
                $ctrl.budgetItem.isEditable = true;
                $ctrl.budgetItem.credit = $ctrl.availableCredit[0];
            } else {
                zemCampaignBudgetsEndpoint.get(
                    $ctrl.campaign.id,
                    $ctrl.selectedBudgetId
                ).then(function (data) {
                    var creditStartDate = moment(data.startDate, 'MM/DD/YYYY').toDate(),
                        creditEndDate = moment(data.endDate, 'MM/DD/YYYY').toDate();

                    $ctrl.budgetItem = data;
                    $ctrl.budgetItem.startDate = creditStartDate;
                    $ctrl.budgetItem.endDate = creditEndDate;
                    $ctrl.budgetItem.margin = $filter('number')(
                        $ctrl.budgetItem.margin.replace('%', ''),
                        2
                    );

                    $ctrl.initStartDate = $ctrl.minDate;
                    $ctrl.initEndDate = $ctrl.maxDate;

                    $ctrl.canDelete = data.state == constants.budgetLineItemStatus.PENDING;
                    $ctrl.availableCredit = getAvailableCredit(false, data.credit.id);
                    $ctrl.minDate = creditStartDate;
                    $ctrl.maxDate = moment($ctrl.availableCredit[0].endDate, 'MM/DD/YYYY').toDate();
                });
            }
        };

        function closeModal (data) {
            $timeout(function () {
                $ctrl.saveRequestInProgress = false;
                $ctrl.modalInstance.close(data);
            }, 1000);
        }

        function updateBudgetInitialValues (credit) {
            var creditStartDate = moment(credit.startDate, 'MM/DD/YYYY').toDate(),
                creditEndDate = moment(credit.endDate, 'MM/DD/YYYY').toDate(),
                today = moment().toDate();

            $ctrl.minDate = creditStartDate;
            $ctrl.maxDate = creditEndDate;
            $ctrl.initEndDate = null;
            $ctrl.initStartDate = creditStartDate > today ? creditStartDate : today;

            $ctrl.budgetItem.startDate = $ctrl.initStartDate;
            $ctrl.budgetItem.endDate = $ctrl.initEndDate;
            $ctrl.budgetItem.amount = null;
        }

        function getAvailableCredit (all, include) {
            return all ? $ctrl.credits : $ctrl.credits.filter(function (obj) {
                return include && obj.id === include || !include && obj.isAvailable;
            });
        }
    }
});
