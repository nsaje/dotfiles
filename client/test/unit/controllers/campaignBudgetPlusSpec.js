/* global it, describe, module, expect, inject, beforeEach */
'use strict';

describe('CampaignBudgetCtrl', function () {
    var $scope, $state, api;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(function () {
        inject(function ($rootScope, $controller, _$state_) {
            $scope = $rootScope.$new();

            $scope.isPermissionInternal = function () {
                return true;
            };
            $scope.hasPermission = function () {
                return true;
            };
            $scope.campaign = {id: 1};

            var mockApiFunc = function () {
                return {
                    then: function () {
                        return {
                            finally: function () {},
                        };
                    },
                };
            };

            api = {
                campaignBudget: {
                    list: mockApiFunc,
                    save: mockApiFunc,
                    create: mockApiFunc,
                    get: mockApiFunc,
                    delete: mockApiFunc,
                    convert: {errors: function (obj) {
                        return obj;
                    }},
                },
            };

            $state = _$state_;
            $state.params = {id: 1};

            $controller('CampaignBudgetCtrl', {$scope: $scope, api: api});
        });
    });

    describe('addBudgetItem', function () {
        it('sets selected budget item to null', function () {
            $scope.addBudgetItem();
            expect($scope.selectedBudgetId).toBe(null);
        });

        it('opens a modal', function () {
            $scope.addBudgetItem().result.catch(function (error) {
                expect(error).toBeUndefined();
            });
        });
    });

    describe('editBudgetItem', function () {
        it('sets selected budget item correctly', function () {
            $scope.editBudgetItem(10);
            expect($scope.selectedBudgetId).toBe(10);
        });

        it('opens a modal', function () {
            $scope.editBudgetItem(10).result.catch(function (error) {
                expect(error).toBeUndefined();
            });
        });
    });

});
