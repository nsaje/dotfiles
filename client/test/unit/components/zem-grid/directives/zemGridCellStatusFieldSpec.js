/* globals describe, it, beforeEach, expect, module, inject */

describe('zemGridCellStatusField', function () {
    var scope, element, $compile;

    var template = '<zem-grid-cell-status-field data="ctrl.data" row="ctrl.row" grid="ctrl.grid"></zem-grid-cell-status-field>'; // eslint-disable-line max-len

    beforeEach(module('one'));

    beforeEach(inject(function ($rootScope, _$compile_) {
        $compile = _$compile_;

        scope = $rootScope.$new();
        scope.ctrl = {};
        scope.ctrl.grid = {
            meta: {
                data: {
                    level: '',
                    breakdown: '',
                },
                pubsub: {
                    register: function () {},
                    EVENTS: {DATA_UPDATED: ''},
                },
            },
        };
    }));

    it('should set status text to empty string by default', function () {
        scope.ctrl.row = {
            data: {
                stats: {},
            },
        };

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.statusText).toEqual('');
    });

    it('should set status text correctly for archived rows', function () {
        scope.ctrl.row = {
            archived: true,
        };

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.statusText).toEqual('Archived');
    });

    it('should set status text correctly for different levels and breakdowns', function () {
        var tests = [
            // TODO: Add tests for other levels and breakdowns
            {level: 'campaigns', breakdown: 'ad_group', field: 'state', value: 1, expectedResult: 'Active'},
            {level: 'campaigns', breakdown: 'ad_group', field: 'state', value: 2, expectedResult: 'Paused'},
            {level: 'campaigns', breakdown: 'source', field: 'status', value: 1, expectedResult: 'Active'},
            {level: 'campaigns', breakdown: 'source', field: 'status', value: 2, expectedResult: 'Paused'},
            {level: 'unknown', breakdown: 'unknown', field: 'unknown', value: null, expectedResult: ''},
        ];

        tests.forEach(function (test) {
            scope.ctrl.grid.meta.data = {
                level: test.level,
                breakdown: test.breakdown,
            };

            scope.ctrl.row = {
                archived: false,
                data: {stats: {}},
            };
            scope.ctrl.row.data.stats[test.field] = {value: test.value};

            element = $compile(template)(scope);
            scope.$digest();

            expect(element.isolateScope().ctrl.statusText).toEqual(test.expectedResult);
        });
    });

    it('should update status text on row or data change', function () {
        scope.ctrl.row = {
            archived: true,
        };

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.statusText).toEqual('Archived');

        scope.ctrl.row = {
            archived: false,
            data: {
                stats: {},
            },
        };
        scope.$digest();

        expect(element.isolateScope().ctrl.statusText).toEqual('');
    });
});
