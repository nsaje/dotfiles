/* global module,beforeEach,it,describe,expect,inject,constants */
'use strict';

describe('zemSideTabset', function () {
    var scope, sideBar, isolate;

    beforeEach(module('one'));
    beforeEach(inject(function ($rootScope, $compile) {
        scope = $rootScope.$new();

        sideBar = '<zem-side-tabset selected="selectedSideTab.tab" zem-has-permission="hasPermission" zem-has-permission-internal="hasPermissionInternal"/>'; // eslint-disable-line max-len


        scope.selectedSideTab = {
            tab: undefined,
        };
        scope.hasPermission = function () {
            return true;
        };
        scope.isPermissionInternal = function () {
            return false;
        };

        sideBar = $compile(sideBar)(scope);
        scope.$digest();

        isolate = sideBar.isolateScope();
        isolate.$digest();
    }));

    it('should initialize correctly', function () {
        expect(isolate.visibleTabCount).toEqual(2);
        expect(isolate.selected.type).toEqual(
            constants.sideBarTabs.PERFORMANCE
        );
    });
});
