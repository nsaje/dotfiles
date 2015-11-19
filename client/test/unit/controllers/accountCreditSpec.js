'use strict';

describe('AccountCreditCtrl', function () {
    var $modalStack, $scope, $state, $q, api;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(function () {
        inject(function ($rootScope, $controller, _$state_, _$q_, _$modalStack_) {
            $q = _$q_;
            $scope = $rootScope.$new();

            $scope.isPermissionInternal = function() {return true;};
            $scope.hasPermission = function() {return true;};
            $scope.account = {id: 1};

            var mockApiFunc = function() {
                return {
                    then: function() {
                        return {
                            finally: function() {}
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
                    convert: { errors: function (obj) { return obj; } }
                }
            };

            $state = _$state_;
            $state.params = {id: 1};

            $modalStack = _$modalStack_;

            $controller('AccountCreditCtrl', { $scope: $scope, api: api });
        });
    });

    describe('addCreditItem', function (done) {
        it('sets selected credit item to null', function () {
            $scope.addCreditItem();
            expect($scope.selectedCreditItemId).toBe(null);
        });

        it('opens a modal', function () {
            $scope.addCreditItem().result.catch(function(error) {
                expect(error).toBeUndefined();
            }).finally(done);
        });
    });

    describe('editCreditItem', function (done) {
        it('sets selected credit item correctly', function () {
            $scope.editCreditItem(10);
            expect($scope.selectedCreditItemId).toBe(10);
        });

        it('opens a modal', function () {
            $scope.editCreditItem(10).result.catch(function(error) {
                expect(error).toBeUndefined();
            }).finally(done);
        });
    });

});
