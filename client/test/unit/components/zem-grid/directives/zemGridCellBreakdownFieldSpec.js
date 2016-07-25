/* globals describe, it, beforeEach, expect, module, inject */

describe('zemGridCellBreakdownField', function () {
    var scope, element, $compile;

    var template = '<zem-grid-cell-breakdown-field data="ctrl.data" row="ctrl.row" column="ctrl.col" grid="ctrl.grid"></zem-grid-cell-breakdown-field>'; // eslint-disable-line max-len

    beforeEach(module('one'));

    beforeEach(inject(function ($rootScope, _$compile_) {
        $compile = _$compile_;

        scope = $rootScope.$new();
        scope.ctrl = {};
        scope.ctrl.grid = {
            meta: createMockGridMeta(),
        };
    }));

    function createMockGridMeta () {
        return {
            data: {
                level: '',
                breakdown: '',
            },
            dataService: {
                getBreakdownLevel: function () {
                },
            },
            collapseService: {
                isRowCollapsable: function () {
                },
                isRowCollapsed: function () {
                },
            },
            pubsub: {
                EVENTS: {},
                register: function () {
                },
            }
        };
    }

    it('should set field type to baseField by default', function () {
        scope.ctrl.row = {};

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.fieldType).toEqual('baseField');
    });

    it('should set field type to totalsLabel for footer row', function () {
        scope.ctrl.row = {level: 0};

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.fieldType).toEqual('totalsLabel');
    });

    it('should set field type to baseField for rows on level > 1', function () {
        scope.ctrl.row = {level: 2};

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.fieldType).toEqual('baseField');
    });

    it('should set field type to internalLink for rows on first level only if breakdown has internal links', function () { // eslint-disable-line max-len
        var tests = [
            {breakdown: 'account', expectedResult: 'internalLink'},
            {breakdown: 'campaign', expectedResult: 'internalLink'},
            {breakdown: 'ad_group', expectedResult: 'internalLink'},
            {breakdown: 'content_ad', expectedResult: 'baseField'},
            {breakdown: 'source', expectedResult: 'baseField'},
            {breakdown: 'publisher', expectedResult: 'baseField'},
        ];

        scope.ctrl.row = {level: 1};

        tests.forEach(function (test) {
            var meta = createMockGridMeta();
            meta.data.breakdown = test.breakdown;
            scope.ctrl.grid = {meta: meta};

            element = $compile(template)(scope);
            scope.$digest();

            expect(element.isolateScope().ctrl.fieldType).toEqual(test.expectedResult);
        });
    });

    it('should show totals label for fields of type totalsLabel', function () {
        element = $compile(template)(scope);
        scope.$digest();

        element.isolateScope().ctrl.fieldType = 'totalsLabel';
        scope.$digest();

        expect(element.find('.zem-grid-cell-totals-label').hasClass('ng-hide')).toBe(false);
        expect(element.find('.zem-grid-cell-base-breakdown-field').hasClass('ng-hide')).toBe(true);
        expect(element.find('.zem-grid-cell-internal-link').hasClass('ng-hide')).toBe(true);
    });

    it('should show base field for fields of type baseField', function () {
        element = $compile(template)(scope);
        scope.$digest();

        element.isolateScope().ctrl.fieldType = 'baseField';
        scope.$digest();

        expect(element.find('.zem-grid-cell-totals-label').hasClass('ng-hide')).toBe(true);
        expect(element.find('.zem-grid-cell-base-breakdown-field').hasClass('ng-hide')).toBe(false);
        expect(element.find('.zem-grid-cell-internal-link').hasClass('ng-hide')).toBe(true);
    });

    it('should show internal link for fields of type internalLink', function () {
        element = $compile(template)(scope);
        scope.$digest();

        element.isolateScope().ctrl.fieldType = 'internalLink';
        scope.$digest();

        expect(element.find('.zem-grid-cell-totals-label').hasClass('ng-hide')).toBe(true);
        expect(element.find('.zem-grid-cell-base-breakdown-field').hasClass('ng-hide')).toBe(true);
        expect(element.find('.zem-grid-cell-internal-link').hasClass('ng-hide')).toBe(false);
    });
});
