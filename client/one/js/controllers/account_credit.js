/* globals angular, moment */
angular.module('one.legacy').controller('AccountCreditCtrl',
    function ($scope, $state, $uibModal, $location, $window, api, zemDataFilterService) {
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
            var modalInstance = $uibModal.open({
                templateUrl: '/partials/account_credit_item_modal.html',
                controller: 'AccountCreditItemModalCtrl',
                scope: $scope,
                backdrop: 'static',
                keyboard: false,
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
            if (!$window.confirm('Are you sure you want to cancel the credit line item?')) {
                return;
            }
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
            $scope.setActiveTab();
        };

        var dateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(refresh);
        $scope.$on('$destroy', dateRangeUpdateHandler);
        $scope.init();
    });
