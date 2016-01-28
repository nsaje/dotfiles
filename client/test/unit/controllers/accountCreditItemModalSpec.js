describe('AccountCreditItemModalCtrl', function () {
    var $scope, $modalInstance, api, $q, $window, $timeout, openedDeferred;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function ($controller, $rootScope, _$q_, _$timeout_, _$window_) {
        $q = _$q_;
        $timeout = _$timeout_;
        $scope = $rootScope.$new();
        $scope.account = {
            id: 1
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
            accountCredit: {
                list: mockApiFunc,
                save: mockApiFunc,
                create: mockApiFunc,
                get: mockApiFunc,
                delete: mockApiFunc,
                convert: {errors: function (obj) { return obj; }}
            }
        };

        $controller(
            'AccountCreditItemModalCtrl',
            {$scope: $scope, $modalInstance: $modalInstance, api: api}
        );
    }));

    describe('upsertCreditItem', function () {
        it('calls correct api function on create and closes the modal', function () {
            var deferred = $q.defer();
            $scope.creditItem = {
                id: 1
            };
            $scope.isNew = true;

            spyOn($modalInstance, 'close');
            spyOn(api.accountCredit, 'create').and.callFake(function () { return deferred.promise; });

            $scope.upsertCreditItem();

            deferred.resolve(1);
            $scope.$digest();

            expect(api.accountCredit.create).toHaveBeenCalled();
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
            spyOn(api.accountCredit, 'save').and.callFake(function () { return deferred.promise; });

            $scope.upsertCreditItem();

            deferred.resolve(1);
            $scope.$digest();

            expect(api.accountCredit.save).toHaveBeenCalled();
            $timeout(function () {
                expect($modalInstance.close).toHaveBeenCalled();
            }, 1500);

        });
    });

    describe('discardCreditItem', function (done) {
        it('closes the modal', function () {
            spyOn($modalInstance, 'close');
            $scope.discardCreditItem();
            $scope.$digest();
            $timeout(function () {
                expect($modalInstance.close).toHaveBeenCalled();
            }, 1200);
        });
    });

    describe('deleteCreditItem', function () {
        it ('forces user confirmation', function () {
            var deferred = $q.defer();
            $window.confirm = function () { return true; };

            spyOn($modalInstance, 'close');
            spyOn(api.accountCredit, 'delete').and.callFake(function () {
                return deferred.promise;
            });

            $scope.deleteCreditItem(10);
            deferred.resolve();
            $scope.$digest();

            expect(api.accountCredit.delete).toHaveBeenCalled();
            $timeout(function () {
                expect($modalInstance.close).toHaveBeenCalled();
            }, 1500);
        });

        it ('does nothing if user cancels the action', function () {
            var deferred = $q.defer();
            $window.confirm = function () { return false; };

            spyOn($modalInstance, 'close');
            spyOn(api.accountCredit, 'delete').and.callFake(function () {
                return deferred.promise;
            });

            $scope.deleteCreditItem(10);
            $scope.$digest();

            expect(api.accountCredit.delete).not.toHaveBeenCalled();
            $timeout(function () {
                expect($modalInstance.close).not.toHaveBeenCalled();
            }, 1500);
        });
    });

    describe('init', function () {
        it ('sets variables correctly for new items', function () {
            $scope.selectedCreditItemId = null;
            $scope.init();
            $scope.$digest();

            expect($scope.isNew).toBe(true);
            expect($scope.wasSigned).toBe(false);
            expect($scope.canDelete).toBe(false);
            expect($scope.minDate).toBe($scope.today);
        });

        it ('sets variables correctly for existing items', function () {
            var deferred = $q.defer();
            $scope.selectedCreditItemId = 1;

            spyOn(api.accountCredit, 'get').and.callFake(function () {
                return deferred.promise;
            });

            $scope.init();

            deferred.resolve({
                id: 1,
                isSigned: true,
                endDate: '12/31/2015',
                startDate: '12/1/2015',
                licenseFee: '15%'
            });

            $scope.$digest();

            expect($scope.isNew).toBe(false);
            expect($scope.wasSigned).toBe(true);
            expect($scope.canDelete).toBe(false);
            expect($scope.minDate).toBe('12/31/2015');

            expect(api.accountCredit.get).toHaveBeenCalled();
        });
    });
});
