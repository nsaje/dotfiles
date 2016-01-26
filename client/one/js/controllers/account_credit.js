/* globals oneApp, moment */
oneApp.controller('AccountCreditCtrl',
    ['$scope', '$state', '$modal', '$location', '$window', 'api',
    function ($scope, $state, $modal, $location, $window, api) {
        function error () {}
        function refresh (updatedId) {
            $scope.updatedId = updatedId;
            $scope.init();
        }
        function updateView (data) {
            $scope.creditTotals = data.totals;
            $scope.activeCredit = data.active;
            $scope.pastCredit = data.past;
        }
        function openModal () {
            var modalInstance = $modal.open({
                templateUrl: '/partials/account_credit_item_modal.html',
                controller: 'AccountCreditItemModalCtrl',
                windowClass: 'modal',
                scope: $scope,
                backdrop: 'static',
                size: 'wide',
            });
            modalInstance.result.then(refresh);
            return modalInstance;
        }

        $scope.creditTotals = {};
        $scope.canceledIds = {};
        $scope.activeCredit = [];
        $scope.pastCredit = [];

        $scope.isSelected = function (creditStartDate, creditEndDate) {
            var urlStartDate = moment($location.search().start_date).toDate(),
                urlEndDate = moment($location.search().end_date).toDate();

            creditStartDate = moment(creditStartDate, 'MM/DD/YYYY').toDate();
            creditEndDate = moment(creditEndDate, 'MM/DD/YYYY').toDate();

            return urlStartDate <= creditEndDate && urlEndDate >= creditStartDate;
        };

        $scope.$watch('dateRange', function (newValue, oldValue) {
            if (newValue.startDate.isSame(oldValue.startDate) && newValue.endDate.isSame(oldValue.endDate)) {
                return;
            }
            refresh();
        });

        $scope.addCreditItem = function () {
            $scope.canceledIds = {};
            $scope.selectedCreditItemId = null;
            return openModal();
        };

        $scope.editCreditItem = function (id) {
            $scope.canceledIds = {};
            $scope.selectedCreditItemId = id;
            return openModal();
        };

        $scope.cancelCreditItem = function (id) {
            if (!$window.confirm('Are you sure you want to cancel the credit line item?')) { return; }
            api.accountCredit.cancel($scope.account.id, [id]).then(function (response) {
                $scope.canceledIds = {};
                response.canceled.forEach(function (canceledId) {
                    $scope.canceledIds[canceledId] = true;
                });
                refresh();
            });
        };

        $scope.init = function () {
            if (!$scope.account) {
                return;
            }
            $scope.loadingInProgress = true;
            api.accountCredit.list($scope.account.id).then(function (data) {
                $scope.loadingInProgress = false;
                updateView(data);
            }, function () {
                $scope.loadingInProgress = false;
                error();
            });
        };

        $scope.init();
    }]);
