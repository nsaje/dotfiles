describe('zemGridCellBreakdownField', function() {
    var scope, element, $compile;

    var template =
        '<zem-grid-cell-breakdown-field data="ctrl.data" row="ctrl.row" column="ctrl.col" grid="ctrl.grid"></zem-grid-cell-breakdown-field>'; // eslint-disable-line max-len

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($rootScope, _$compile_) {
        $compile = _$compile_;

        scope = $rootScope.$new();
        scope.ctrl = {};
        scope.ctrl.grid = {
            meta: createMockGridMeta(),
        };
    }));

    function createMockGridMeta() {
        return {
            data: {
                level: '',
                breakdown: '',
            },
            dataService: {
                getBreakdownLevel: function() {},
            },
            collapseService: {
                isRowCollapsable: function() {},
                isRowCollapsed: function() {},
            },
            pubsub: {
                EVENTS: {},
                register: function() {},
            },
        };
    }

    it('should set field type to baseField by default', function() {
        scope.ctrl.row = {};

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.fieldType).toEqual('baseField');
    });

    it('should set field type to totalsLabel for footer row', function() {
        scope.ctrl.row = {level: 0};

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.fieldType).toEqual('totalsLabel');
    });

    it('should set field type to baseField in rows for entities without links', function() {
        scope.ctrl.row = {entity: null};

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.fieldType).toEqual('baseField');
    });

    it('should set correct field type based on row entity type', function() {
        var tests = [
            {entityType: 'account', expectedResult: 'internalLink'},
            {entityType: 'campaign', expectedResult: 'internalLink'},
            {entityType: 'adGroup', expectedResult: 'internalLink'},
            {entityType: 'contentAd', expectedResult: 'externalLink'},
            {entityType: 'source', expectedResult: 'baseField'},
            {entityType: 'publisher', expectedResult: 'baseField'},
        ];

        tests.forEach(function(test) {
            var meta = createMockGridMeta();
            scope.ctrl.grid = {meta: meta};
            scope.ctrl.row = {entity: {type: test.entityType}};

            element = $compile(template)(scope);
            scope.$digest();

            expect(element.isolateScope().ctrl.fieldType).toEqual(
                test.expectedResult
            );
        });
    });

    it('should show totals label for fields of type totalsLabel', function() {
        element = $compile(template)(scope);
        scope.$digest();

        element.isolateScope().ctrl.fieldType = 'totalsLabel';
        scope.$digest();

        expect(
            element.find('.zem-grid-cell-totals-label').hasClass('ng-hide')
        ).toBe(false);
        expect(
            element
                .find('.zem-grid-cell-base-breakdown-field')
                .hasClass('ng-hide')
        ).toBe(true);
        expect(
            element.find('.zem-grid-cell-internal-link').hasClass('ng-hide')
        ).toBe(true);
    });

    it('should show base field for fields of type baseField', function() {
        element = $compile(template)(scope);
        scope.$digest();

        element.isolateScope().ctrl.fieldType = 'baseField';
        scope.$digest();

        expect(
            element.find('.zem-grid-cell-totals-label').hasClass('ng-hide')
        ).toBe(true);
        expect(
            element
                .find('.zem-grid-cell-base-breakdown-field')
                .hasClass('ng-hide')
        ).toBe(false);
        expect(
            element.find('.zem-grid-cell-internal-link').hasClass('ng-hide')
        ).toBe(true);
    });

    it('should show internal link for fields of type internalLink', function() {
        element = $compile(template)(scope);
        scope.$digest();

        element.isolateScope().ctrl.fieldType = 'internalLink';
        scope.$digest();

        expect(
            element.find('.zem-grid-cell-totals-label').hasClass('ng-hide')
        ).toBe(true);
        expect(
            element
                .find('.zem-grid-cell-base-breakdown-field')
                .hasClass('ng-hide')
        ).toBe(true);
        expect(
            element.find('.zem-grid-cell-internal-link').hasClass('ng-hide')
        ).toBe(false);
    });
});
