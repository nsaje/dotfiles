/* globals describe, it, inject, module, beforeEach, expect, spyOn */
'use strict';

describe('zemRetargeting', function () {
    var $scope, element, isolate, zemFilterService;

    var template = '<zem-retargeting zem-selected-adgroup-ids="selectedIds" zem-account="account"></zem-locations>';

    beforeEach(module('one'));

    beforeEach(inject(function ($compile, $rootScope, _zemFilterService_) {
        $scope = $rootScope.$new();

        $scope.selectedIds = [];
        $scope.account = {
            campaigns: [{
                adGroups: [{id: 1}, {id: 2, archived: true}, {id: 3}],
            }],
        };

        zemFilterService = _zemFilterService_;

        element = $compile(template)($scope);

        $scope.$digest();
        isolate = element.isolateScope();
    }));

    it('adds new ad groups', function () {
        spyOn(zemFilterService, 'isArchivedFilterOn').and.returnValue(false);

        isolate.addAdgroup({id: 1});
        $scope.$digest();
        expect($scope.selectedIds).toEqual([1]);
        expect(isolate.availableAdgroups().length).toBe(1);
        expect(isolate.availableAdgroups()[0].id).toBe(3);

        isolate.addAdgroup({id: 3});
        $scope.$digest();
        expect($scope.selectedIds).toEqual([1, 3]);
        expect(isolate.availableAdgroups().length).toBe(0);
    });

    it('removes selected ad groups', function () {
        spyOn(zemFilterService, 'isArchivedFilterOn').and.returnValue(false);

        $scope.selectedIds = [1, 3];
        $scope.$digest();

        isolate.removeSelectedAdgroup({id: 1});
        $scope.$digest();
        expect($scope.selectedIds).toEqual([3]);
        expect(isolate.availableAdgroups().length).toBe(1);
        expect(isolate.availableAdgroups()[0].id).toBe(1);

        isolate.removeSelectedAdgroup({id: 3});
        $scope.$digest();
        expect($scope.selectedIds).toEqual([]);
        expect(isolate.availableAdgroups().length).toBe(2);
    });

    it('shows archived ad groups when enabled', function () {
        spyOn(zemFilterService, 'isArchivedFilterOn').and.returnValue(true);
        expect(isolate.availableAdgroups().length).toBe(3);
    });
});
