/* globals angular,oneApp,defaults,moment */
oneApp.controller('CampaignBudgetItemModalCtrl', ['$scope', '$modalInstance', function($scope, $modalInstance) {
    $scope.today = moment().format('M/D/YYYY');
    $scope.isNew = true;
    $scope.getLicenseFees = function(search) {
        // use fresh instance because we modify the collection on the fly
        var fees = ['15', '20', '25'];

        // adds the searched for value to the array
        if (search && fees.indexOf(search) === -1) {
            fees.unshift(search);
        }

        return fees;
    };

    $scope.startDatePicker = {isOpen: false};
    $scope.endDatePicker = {isOpen: false};

    $scope.openDatePicker = function (type) {
        if (type === 'startDate') {
            $scope.startDatePicker.isOpen = true;
        } else if (type === 'endDate') {
            $scope.endDatePicker.isOpen = true;
        }
    };

    $scope.minDate = "10/1/2015";
    $scope.maxDate = "12/1/2015";

    $scope.credits = [
        {id : 1, name: 'Item One ($10.000 available thru 12/1/2015, 20% fee)'},
        {id : 2, name: 'Item Two ($5.000 available thru 11/11/2015, 21% fee)'},
        {id : 3, name: 'Item Three ($22.000 available thru 1/1/2016, 0% fee)'}
    ];
    $scope.numOfCredits = $scope.credits.length;
}]);
