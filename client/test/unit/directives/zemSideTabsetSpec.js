'use strict';

describe('zemSideTabset', function () {
    var scope, sideBar, isolate;
    var data = {
        id: 'totals',
        groups: [{
            id: 'totals',
            name: 'Totals',
            seriesData: {
                cost: [
                    ['2014-07-10', 205.1312],
                    ['2014-07-11', 128.5189],
                ],
            },
        }]
    };

    beforeEach(module('one'));
    beforeEach(inject(function ($rootScope, $compile) {
        scope = $rootScope.$new();

        sideBar = '<zem-side-tabset selected="selectedSideTab.tab" zem-has-permission="hasPermission" zem-has-permission-internal="hasPermissionInternal"/>';

        scope.selectedSideTab = {
            tab: undefined,
        };
        scope.hasPermission = function () {
            return true;
        };
        scope.hasPermissionInternal = function () {
            return true;
        }

        sideBar = $compile(sideBar)(scope);
        scope.$digest();

        isolate = sideBar.isolateScope();
        isolate.$digest();
    }));

    it('should initialize correctly', function () {
        expect(isolate.visibleTabs).toEqual(2);
        expect(isolate.selected).toEqual({
            type: constants.sideBarTabs.PERFORMANCE,
        })
    });
});
