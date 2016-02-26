/* globals describe, it, inject, module, beforeEach, expect, spyOn */
'use strict';

describe('zemRetargeting', function () {
    var $scope, element, isolate, zemFilterService;

    var template = '<zem-retargeting zem-selected-adgroup-ids="selectedAdgroupIds" zem-retargetable-adgroups="retargetableAdgroups" zem-account="account"></zem-locations>'; // eslint-disable-line max-len


    beforeEach(module('one'));

    beforeEach(inject(function ($compile, $rootScope, _zemFilterService_) {
        $scope = $rootScope.$new();

        zemFilterService = _zemFilterService_;

        $scope.selectedAdgroupIds = [];
        $scope.retargetableAdgroups = [
            {
                id: 1,
                archived: false,
            },
            {
                id: 2,
                archived: true,
            },
            {
                id: 3,
                archived: false,
            },
        ];
        $scope.account = {id: 1};

        element = $compile(template)($scope);

        $scope.$digest();
        isolate = element.isolateScope();
    }));

    it('adds new ad groups', function () {
        spyOn(zemFilterService, 'isArchivedFilterOn').and.returnValue(false);

        isolate.addAdgroup({id: 1});
        $scope.$digest();
        expect($scope.selectedAdgroupIds).toEqual([1]);
        expect(isolate.availableAdgroups().length).toBe(1);
        expect(isolate.availableAdgroups()[0].id).toBe(3);

        isolate.addAdgroup({id: 3});
        $scope.$digest();
        expect($scope.selectedAdgroupIds).toEqual([1, 3]);
        expect(isolate.availableAdgroups().length).toBe(0);
    });

    it('removes selected ad groups', function () {
        spyOn(zemFilterService, 'isArchivedFilterOn').and.returnValue(false);

        $scope.selectedAdgroupIds = [1, 3];
        $scope.$digest();

        isolate.removeSelectedAdgroup({id: 1});
        $scope.$digest();
        expect($scope.selectedAdgroupIds).toEqual([3]);
        expect(isolate.availableAdgroups().length).toBe(1);
        expect(isolate.availableAdgroups()[0].id).toBe(1);

        isolate.removeSelectedAdgroup({id: 3});
        $scope.$digest();
        expect($scope.selectedAdgroupIds).toEqual([]);
        expect(isolate.availableAdgroups().length).toBe(2);
    });

    it('shows archived ad groups when enabled', function () {
        spyOn(zemFilterService, 'isArchivedFilterOn').and.returnValue(true);
        expect(isolate.availableAdgroups().length).toBe(3);
    });
});
