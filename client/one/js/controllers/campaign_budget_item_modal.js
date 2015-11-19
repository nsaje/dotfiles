/* globals angular,oneApp,defaults,moment */
oneApp.controller('CampaignBudgetItemModalCtrl', ['$scope', '$modalInstance', '$timeout', 'api', function($scope, $modalInstance, $timeout, api) {
    $scope.today = moment().format('M/D/YYYY');
    $scope.isNew = true;
    $scope.startDatePicker = { isOpen: false };
    $scope.endDatePicker = { isOpen: false };
    $scope.isLoadingInProgress = false;
    $scope.canDelete = false;
    $scope.budgetItem = {};
    $scope.errors = {};
    $scope.minDate = null;
    $scope.maxDate = null;
    $scope.saveRequestInProgress = false;
    
    $scope.initStartDate = null; 
    $scope.endStartDate = null; 
    
    $scope.getLicenseFees = function(search) {
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
            console.log('delam', $scope.budgetItem.credit)
            var id = $scope.budgetItem.credit.id;
            $scope.getAvailableCredit().forEach(function (obj) {
                if (obj.id !== id) { return; }
            
                $scope.minDate = obj.startDate;
                $scope.maxDate = obj.endDate;
                $scope.initStartDate = moment($scope.minDate, 'MM/DD/YYYY').toDate();
                $scope.initEndDate = moment($scope.maxDate, 'MM/DD/YYYY').toDate();
                $scope.budgetItem.amount = obj.total;
                $scope.budgetItem.startDate = $scope.initStartDate;
                $scope.budgetItem.endDate = $scope.initEndDate;
            });
        }, 100); // to be sure that the selected id is correct
        
    };

    $scope.upsertBudgetItem = function () {
        $scope.saveRequestInProgress = true;
        $scope.budgetItem.id = $scope.selectedBudgetId;
        api.campaignBudgetPlus[
            $scope.isNew ? 'create' : 'save'
        ]($scope.campaign.id, $scope.budgetItem).then(function (data) {
            $scope.saved = true;
            $timeout(function () {
                $modalInstance.close(data || null);
            }, 1000);
        }, function (resp) {
            $scope.errors = api.campaignBudgetPlus.convert.error(resp);
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
        if (!confirm("Are you sure you want to delete the budget line item?")) { return; }
        api.campaignBudgetPlus.delete($scope.campaign.id, $scope.selectedBudgetId).then(function () {
            closeModal();
        });
    };

    $scope.init = function () {
        $scope.saveRequestInProgress = false;
        $scope.isNew = $scope.selectedBudgetId === null;
        
        $scope.minDate = $scope.getAvailableCredit()[0].startDate;
        $scope.maxDate = $scope.getAvailableCredit()[0].endDate;
        $scope.initStartDate = moment($scope.minDate, 'MM/DD/YYYY').toDate();
        $scope.initEndDate = moment($scope.maxDate, 'MM/DD/YYYY').toDate();
        $scope.discarded = false;

        if ($scope.isNew) {
            $scope.budgetItem.startDate = $scope.initStartDate;
            $scope.budgetItem.endDate = $scope.initEndDate;
            
            $scope.budgetItem.credit = $scope.getAvailableCredit()[0];
            
            $scope.budgetItem.amount = $scope.getAvailableCredit()[0].total;
            $scope.availableCredit = $scope.getAvailableCredit(false);
        } else {
            api.campaignBudgetPlus.get(
                $scope.campaign.id,
                $scope.selectedBudgetId
            ).then(function (data) {
                $scope.budgetItem = data;
                
                $scope.minDate = data.startDate;
                $scope.maxDate = data.endDate;
                $scope.initStartDate = moment($scope.minDate, 'MM/DD/YYYY').toDate();
                $scope.initEndDate = moment($scope.maxDate, 'MM/DD/YYYY').toDate();

                $scope.canDelete = data.state == constants.budgetLineItemStatus.PENDING;
                $scope.availableCredit = $scope.getAvailableCredit(false, data.credit.id);
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
