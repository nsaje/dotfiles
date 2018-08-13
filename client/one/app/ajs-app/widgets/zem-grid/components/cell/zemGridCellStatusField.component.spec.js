describe('zemGridCellStatusField', function() {
    var scope, element, $compile;

    var template =
        '<zem-grid-cell-status-field data="ctrl.data" row="ctrl.row" grid="ctrl.grid"></zem-grid-cell-status-field>'; // eslint-disable-line max-len

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($rootScope, _$compile_) {
        $compile = _$compile_;

        scope = $rootScope.$new();
        scope.ctrl = {};
        scope.ctrl.row = {};
        scope.ctrl.data = {};
        scope.ctrl.grid = {
            meta: {
                data: {
                    level: '',
                    breakdown: '',
                },
                pubsub: {
                    register: function() {},
                    EVENTS: {DATA_UPDATED: ''},
                },
            },
        };
    }));

    it('should set status text to empty string by default', function() {
        scope.ctrl.row = {
            data: {
                stats: {},
            },
        };

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.statusText).toEqual('');
    });

    it('should set status text correctly for archived rows', function() {
        scope.ctrl.row = {
            archived: true,
        };

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.statusText).toEqual('Archived');
    });

    it('should set status text correctly for different levels and breakdowns', function() {
        var tests = [
            {
                level: 'all_accounts',
                breakdown: 'account',
                value: 1,
                expectedResult: 'Active',
            },
            {
                level: 'all_accounts',
                breakdown: 'account',
                value: 2,
                expectedResult: 'Paused',
            },
            {
                level: 'accounts',
                breakdown: 'campaign',
                value: 1,
                expectedResult: 'Active',
            },
            {
                level: 'accounts',
                breakdown: 'campaign',
                value: 2,
                expectedResult: 'Paused',
            },
            {
                level: 'campaigns',
                breakdown: 'ad_group',
                value: 1,
                expectedResult: 'Active',
            },
            {
                level: 'campaigns',
                breakdown: 'ad_group',
                value: 2,
                expectedResult: 'Paused',
            },
            {
                level: 'all_accounts',
                breakdown: 'source',
                value: 1,
                expectedResult: 'Active',
            },
            {
                level: 'all_accounts',
                breakdown: 'source',
                value: 2,
                expectedResult: 'Paused',
            },
            {
                level: 'accounts',
                breakdown: 'source',
                value: 1,
                expectedResult: 'Active',
            },
            {
                level: 'accounts',
                breakdown: 'source',
                value: 2,
                expectedResult: 'Paused',
            },
            {
                level: 'campaigns',
                breakdown: 'source',
                value: 1,
                expectedResult: 'Active',
            },
            {
                level: 'campaigns',
                breakdown: 'source',
                value: 2,
                expectedResult: 'Paused',
            },
            {
                level: 'ad_groups',
                breakdown: 'source',
                value: 1,
                expectedResult: 'Active',
            },
            {
                level: 'ad_groups',
                breakdown: 'source',
                value: 2,
                expectedResult: 'Paused',
            },
            {
                level: 'ad_groups',
                breakdown: 'publisher',
                value: 1,
                expectedResult: 'Whitelisted',
            },
            {
                level: 'ad_groups',
                breakdown: 'publisher',
                value: 2,
                expectedResult: 'Blacklisted',
            },
            {
                level: 'ad_groups',
                breakdown: 'publisher',
                value: 3,
                expectedResult: 'Active',
            },
            {
                level: 'unknown',
                breakdown: 'unknown',
                value: null,
                expectedResult: '',
            },
        ];

        tests.forEach(function(test) {
            scope.ctrl.grid.meta.data = {
                level: test.level,
                breakdown: test.breakdown,
            };

            scope.ctrl.row = {
                archived: false,
            };
            scope.ctrl.data = {value: test.value};

            element = $compile(template)(scope);
            scope.$digest();

            expect(element.isolateScope().ctrl.statusText).toEqual(
                test.expectedResult
            );
        });
    });

    it('should update status text on row or data change', function() {
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
