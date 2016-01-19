'use strict';

describe('CampaignBudgetPlusCtrl', function () {
    var $modalStack, $scope, $state, $q, api;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(function () {
        inject(function ($rootScope, $controller, _$state_, _$q_, _$modalStack_) {
            $q = _$q_;
            $scope = $rootScope.$new();

            $scope.isPermissionInternal = function() {return true;};
            $scope.hasPermission = function() {return true;};
            $scope.campaign = {id: 1};

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
                campaignBudgetPlus: {
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

            $controller('CampaignBudgetPlusCtrl', { $scope: $scope, api: api });
        });
    });

    describe('addBudgetItem', function (done) {
        it('sets selected budget item to null', function () {
            $scope.addBudgetItem();
            expect($scope.selectedBudgetId).toBe(null);
        });

        it('opens a modal', function () {
            $scope.addBudgetItem().result.catch(function(error) {
                expect(error).toBeUndefined();
            }).finally(done);
        });
    });

    describe('editBudgetItem', function (done) {
        it('sets selected budget item correctly', function () {
            $scope.editBudgetItem(10);
            expect($scope.selectedBudgetId).toBe(10);
        });

        it('opens a modal', function () {
            $scope.editBudgetItem(10).result.catch(function(error) {
                expect(error).toBeUndefined();
            }).finally(done);
        });
    });

});
