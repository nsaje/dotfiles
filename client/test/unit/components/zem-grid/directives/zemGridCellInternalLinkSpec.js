/* globals describe, it, beforeEach, expect, module, inject */

describe('zemGridCellInternalLink', function () {
    var scope, element, $compile;

    var template = '<zem-grid-cell-internal-link data="ctrl.data" row="ctrl.row" column="ctrl.column" grid="ctrl.grid"></zem-grid-cell-internal-link>'; // eslint-disable-line max-len

    beforeEach(module('one'));

    beforeEach(inject(function ($rootScope, _$compile_) {
        $compile = _$compile_;

        scope = $rootScope.$new();
        scope.ctrl = {};
        scope.ctrl.data = {};
        scope.ctrl.row = {};
        scope.ctrl.grid = {
            meta: {
                data: {
                    level: '',
                },
            },
        };
    }));

    it('should update id and state properties on row or data change', function () {
        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.id).toEqual(-1);
        expect(element.isolateScope().ctrl.state).toEqual('unknown');

        var tests = [
            {level: 'all_accounts', breakdownId: 123, expectedId: 123, expectedState: 'main.accounts.campaigns'},
            {level: 'accounts', breakdownId: 456, expectedId: 456, expectedState: 'main.campaigns.ad_groups'},
            {level: 'campaigns', breakdownId: 789, expectedId: 789, expectedState: 'main.adGroups.ads'},
            {level: 'ad_groups', breakdownId: undefined, expectedId: -1, expectedState: 'unknown'},
        ];

        tests.forEach(function (test) {
            scope.ctrl.row = {
                data: {
                    breakdownId: test.breakdownId,
                },
                level: 1,
            };
            scope.ctrl.grid.meta.data.level = test.level;
            scope.$digest();

            expect(element.isolateScope().ctrl.id).toEqual(test.expectedId);
            expect(element.isolateScope().ctrl.state).toEqual(test.expectedState);
        });
    });
});
