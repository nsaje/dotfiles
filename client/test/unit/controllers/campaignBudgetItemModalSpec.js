describe('CampaignBudgetItemModalCtrl', function () {
    var $scope, $modalInstance, api, $q, $window, $timeout, openedDeferred;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function ($controller, $rootScope, _$q_, _$timeout_, _$window_) {
        $q = _$q_;
        $timeout = _$timeout_;
        $scope = $rootScope.$new();
        $scope.campaign = {
            id: 1
        };
        $scope.getAvailableCredit = function () {
            return [
                {startDate: '12/1/2015', endDate: '12/31/2015', id: 1, licenseFee: '15%'}
            ];
        };

        $window = _$window_;

        openedDeferred = $q.defer();
        $modalInstance = {
            close: function () {},
            opened: openedDeferred.promise
        };

        var mockApiFunc = function () {
            return {
                then: function () {
                    return {
                        finally: function () {}
                    };
                }
            };
        };

        api = {
            campaignBudget: {
                list: mockApiFunc,
                save: mockApiFunc,
                create: mockApiFunc,
                get: mockApiFunc,
                delete: mockApiFunc,
                convert: {errors: function (obj) { return obj; }}
            }
        };

        $controller(
            'CampaignBudgetItemModalCtrl',
            {$scope: $scope, $modalInstance: $modalInstance, api: api}
        );
    }));

    describe('upsertBudgetItem', function () {
        it('calls correct api function on create and closes the modal', function () {
            var deferred = $q.defer();
            $scope.creditItem = {
                id: 1
            };
            $scope.isNew = true;

            spyOn($modalInstance, 'close');
            spyOn(api.campaignBudget, 'create').and.callFake(
                function () { return deferred.promise; }
            );

            $scope.upsertBudgetItem();

            deferred.resolve(1);
            $scope.$digest();

            expect(api.campaignBudget.create).toHaveBeenCalled();
            $timeout(function () {
                expect($modalInstance.close).toHaveBeenCalled();
            }, 1500);
        });

        it('calls correct api function on edit and closes the modal', function () {
            var deferred = $q.defer();
            $scope.creditItem = {
                id: 1
            };
            $scope.isNew = false;

            spyOn($modalInstance, 'close');
            spyOn(api.campaignBudget, 'save').and.callFake(
                function () { return deferred.promise; }
            );

            $scope.upsertBudgetItem();

            deferred.resolve(1);
            $scope.$digest();

            expect(api.campaignBudget.save).toHaveBeenCalled();
            $timeout(function () {
                expect($modalInstance.close).toHaveBeenCalled();
            }, 1500);

        });
    });

    describe('discardBudgetItem', function () {
        it('closes the modal', function () {
            spyOn($modalInstance, 'close');
            $scope.discardBudgetItem();
            $scope.$digest();
            $timeout(function () {
                expect($modalInstance.close).toHaveBeenCalled();
            }, 1200);
        });
    });

    describe('deleteBudgetItem', function () {
        it ('forces user confirmation', function () {
            var deferred = $q.defer();
            $window.confirm = function () { return true; };

            spyOn($modalInstance, 'close');
            spyOn(api.campaignBudget, 'delete').and.callFake(function () {
                return deferred.promise;
            });

            $scope.deleteBudgetItem(10);
            deferred.resolve();
            $scope.$digest();

            expect(api.campaignBudget.delete).toHaveBeenCalled();
            $timeout(function () {
                expect($modalInstance.close).toHaveBeenCalled();
            }, 1500);
        });

        it ('does nothing if user cancels the action', function () {
            var deferred = $q.defer();
            $window.confirm = function () { return false; };

            spyOn($modalInstance, 'close');
            spyOn(api.campaignBudget, 'delete').and.callFake(function () {
                return deferred.promise;
            });

            $scope.deleteBudgetItem(10);
            $scope.$digest();

            expect(api.campaignBudget.delete).not.toHaveBeenCalled();
            $timeout(function () {
                expect($modalInstance.close).not.toHaveBeenCalled();
            }, 1500);
        });
    });

    describe('init', function () {
        it ('sets variables correctly for new items', function () {
            $scope.selectedBudgetId = null;
            $scope.availableCredit = [];
            $scope.init();
            $scope.$digest();

            expect($scope.isNew).toBe(true);
            expect($scope.canDelete).toBe(false);
            expect($scope.availableCredit).toBeTruthy();
            expect($scope.minDate).toBe('12/1/2015');
            expect($scope.maxDate).toBe('12/31/2015');
        });

        it ('sets variables correctly for existing items', function () {
            var deferred = $q.defer();
            $scope.selectedBudgetId = 1;
            $scope.availableCredit = [];

            spyOn(api.campaignBudget, 'get').and.callFake(function () {
                return deferred.promise;
            });

            $scope.init();

            deferred.resolve({
                id: 1,
                endDate: '12/31/2015',
                startDate: '12/1/2015',
                credit: {id: 1, endDate: '12/31/2016'}
            });

            $scope.$digest();

            expect($scope.isNew).toBe(false);
            expect($scope.canDelete).toBe(false);
            expect($scope.minDate).toBe('12/1/2015');
            expect($scope.maxDate).toBe('12/31/2016');
            expect($scope.availableCredit).toBeTruthy();
            expect(api.campaignBudget.get).toHaveBeenCalled();
        });
    });
});
