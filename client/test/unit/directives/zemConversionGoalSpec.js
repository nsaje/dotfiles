'use strict';

describe('zemConversionGoals', function () {
    var $scope, $q, element, isolate;

    var mockApiFunc = function() {
        return {
            then: function() {
                return {
                    finally: function() {}
                };
            }
        };
    };

    var api = {
        conversionGoal: {
            list: mockApiFunc,
            post: mockApiFunc,
            delete: mockApiFunc
        }
    };

    angular.module('conversionGoalsApiMock', []);
    angular.module('conversionGoalsApiMock').service('api', function () {
        return api;
    });

    beforeEach(module('one'));
    beforeEach(module('conversionGoalsApiMock'));

    beforeEach(inject(function ($compile, $rootScope, _$q_) {
        $q =  _$q_;
        var template = '<zem-conversion-goals zem-campaign="campaign" zem-has-permission="hasPermission" zem-is-permission-internal="isPermissionInternal"></zem-conversion-goals>';

        $scope = $rootScope.$new();
        $scope.isPermissionInternal = function() {return true;};
        $scope.hasPermission = function() {return true;};
        $scope.campaign = {id: 1};

        element = $compile(template)($scope);

        $scope.$digest();
        isolate = element.isolateScope();
    }));

    describe('addConversionGoal', function(done) {
        it('opens a modal window', function () {
            isolate.addConversionGoal().result
                .catch(function(error) {
                    expect(error).toBeUndefined();
                })
                .finally(done);
        });
    });

    describe('listConversionGoals', function() {
        beforeEach(function() {
            isolate.conversionPixels = [];
        });

        it('sets error to true on failure', function () {
            var deferred = $q.defer();

            spyOn(api.conversionGoal, 'list').and.callFake(function () {
                return deferred.promise;
            });

            isolate.getConversionGoals();
            isolate.$digest();

            expect(isolate.requestInProgress).toBe(true);

            deferred.reject();
            isolate.$digest();

            expect(isolate.requestInProgress).toBe(false);
            expect(api.conversionGoal.list).toHaveBeenCalled();
            expect(isolate.conversionGoals).toEqual([]);
            expect(isolate.error).toEqual(true);
        });

        it('populates conversion pixels array on success', function () {
            var deferred = $q.defer();

            spyOn(api.conversionGoal, 'list').and.callFake(function () {
                return deferred.promise;
            });

            isolate.getConversionGoals();
            isolate.$digest();

            expect(isolate.requestInProgress).toBe(true);

            deferred.resolve(
                {
                    rows: [{id: 1, type: 2, name: 'conversion goal', conversionWindow: null, goalId: '1'}],
                    availablePixels: [{id: 1, slug: 'slug'}]
                }
            );
            isolate.$digest();

            expect(isolate.requestInProgress).toBe(false);
            expect(api.conversionGoal.list).toHaveBeenCalled();
            var expectedRows = [{id: 1, rows :[{title: 'Name', value: 'conversion goal'}, {title: 'Type', value: 'Google Analytics'}, {title: 'Goal name', value: '1'}]}];
            expect(angular.equals(isolate.conversionGoals, expectedRows)).toEqual(true);
            expect(isolate.availablePixels).toEqual([{id: 1, slug: 'slug'}]);
            expect(isolate.error).toEqual(false);
        });
    });

    describe('removeConversionGoal', function() {
        it('sets error flag on failure', function () {
            var deferred = $q.defer();

            spyOn(api.conversionGoal, 'delete').and.callFake(function() {
                return deferred.promise;
            });

            isolate.conversionGoals = [{id: 1, rows :[{title: 'Name', value: 'conversion goal'}, {title: 'Type', value: 'Google Analytics'}, {title: 'Goal name', value: '1'}]}];
            isolate.removeConversionGoal(1, 1);
            isolate.$digest();

            expect(isolate.requestInProgress).toBe(true);

            deferred.reject();
            isolate.$digest();

            expect(api.conversionGoal.delete).toHaveBeenCalled();
            expect(isolate.error).toBe(true);
            var expectedRows = [{id: 1, rows :[{title: 'Name', value: 'conversion goal'}, {title: 'Type', value: 'Google Analytics'}, {title: 'Goal name', value: '1'}]}];
            expect(angular.equals(isolate.conversionGoals, expectedRows)).toEqual(true);
        });

        it('updates history on success', function() {
            var deferred = $q.defer();

            spyOn(api.conversionGoal, 'delete').and.callFake(function() {
                return deferred.promise;
            });

            isolate.conversionGoals = [{id: 1, rows :[{title: 'Name', value: 'conversion goal'}, {title: 'Type', value: 'Google Analytics'}, {title: 'Goal name', value: '1'}]}];
            isolate.removeConversionGoal(1, 1);
            isolate.$digest();

            expect(isolate.requestInProgress).toBe(true);

            deferred.resolve();
            isolate.$digest();

            expect(api.conversionGoal.delete).toHaveBeenCalled();
            expect(isolate.error).toBe(false);
            expect(isolate.conversionGoals).toEqual([]);
        });
    });
});
