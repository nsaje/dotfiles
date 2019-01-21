describe('zemGridCellInternalLink', function() {
    var scope, element, $compile;

    var template =
        '<zem-grid-cell-internal-link data="ctrl.data" row="ctrl.row" column="ctrl.column" grid="ctrl.grid"></zem-grid-cell-internal-link>'; // eslint-disable-line max-len

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($rootScope, _$compile_) {
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

    it('should update id and state properties on row or data change', function() {
        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.href).toEqual(null);

        var tests = [
            {
                entityType: 'account',
                id: 123,
                expectedHref: '/v2/analytics/account/123',
            },
            {
                entityType: 'campaign',
                id: 456,
                expectedHref: '/v2/analytics/campaign/456',
            },
            {
                entityType: 'adGroup',
                id: 789,
                expectedHref: '/v2/analytics/adgroup/789',
            },
            {
                entityType: 'unknown',
                id: undefined,
                expectedHref: '/v2/analytics/accounts',
            },
        ];

        tests.forEach(function(test) {
            scope.ctrl.row = {
                data: {},
                entity: {
                    type: test.entityType,
                    id: test.id,
                },
            };
            scope.$digest();

            expect(element.isolateScope().ctrl.href).toEqual(test.expectedHref);
        });
    });
});
