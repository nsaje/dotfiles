describe('zemGridCellExternalLink', function() {
    var scope, element, $compile;

    var template =
        '<zem-grid-cell-external-link data="ctrl.data" row="ctrl.row" column="ctrl.column" grid="ctrl.grid"></zem-grid-cell-external-link>'; // eslint-disable-line max-len

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($rootScope, _$compile_) {
        $compile = _$compile_;

        scope = $rootScope.$new();
        scope.ctrl = {};
        scope.ctrl.data = {};
        scope.ctrl.row = {};
        scope.ctrl.column = {};
        scope.ctrl.grid = {};
    }));

    it('should correctyl set field visibility', function() {
        element = $compile(template)(scope);
        scope.$digest();

        element.isolateScope().ctrl.row = {
            level: 1,
        };
        scope.$digest();

        expect(element.isolateScope().ctrl.fieldVisible).toBe(true);

        element.isolateScope().ctrl.row = {
            level: 0,
        };
        element.isolateScope().ctrl.column = {
            data: {
                totalRow: false,
            },
        };
        scope.$digest();

        expect(element.isolateScope().ctrl.fieldVisible).toBe(false);
    });

    it('should show icon link correctly', function() {
        scope.ctrl.data = {
            url: 'example.com',
        };
        scope.ctrl.column = {
            type: 'link',
        };
        element = $compile(template)(scope);
        scope.$digest();

        expect(element.find('.icon-link a').hasClass('ng-hide')).toBe(false);
        expect(
            element.find('.icon-link .link-img-disabled').hasClass('ng-hide')
        ).toBe(true);

        scope.ctrl.data = {
            url: '',
        };
        scope.ctrl.row.data = {
            supplyDashDisabledMessage: 'Disabled',
        };
        scope.$digest();

        expect(element.find('.icon-link a').hasClass('ng-hide')).toBe(true);
        expect(
            element.find('.icon-link .link-img-disabled').hasClass('ng-hide')
        ).toBe(false);
        expect(
            element
                .find('.icon-link .link-img-disabled')
                .attr('zem-lazy-popover-text')
        ).toEqual('Disabled');
    });

    it('should show visible link correctly', function() {
        scope.ctrl.data = {
            url: 'example.com',
        };
        scope.ctrl.column = {
            type: 'visibleLink',
        };
        element = $compile(template)(scope);
        scope.$digest();

        expect(element.find('.visible-link a').hasClass('ng-hide')).toBe(false);

        scope.ctrl.data = {
            url: '',
        };
        scope.$digest();

        expect(element.find('.visible-link a').hasClass('ng-hide')).toBe(true);
    });

    it('should show text link correctly', function() {
        scope.ctrl.data = {
            text: 'Example',
            url: 'example.com',
        };
        scope.ctrl.column = {
            type: 'linkText',
        };
        element = $compile(template)(scope);
        scope.$digest();

        expect(element.find('.text-link a').hasClass('ng-hide')).toBe(false);
        expect(
            element.find('.text-link .text-link-disabled').hasClass('ng-hide')
        ).toBe(true);

        scope.ctrl.data = {
            url: '',
        };
        scope.$digest();

        expect(element.find('.text-link a').hasClass('ng-hide')).toBe(true);
        expect(
            element.find('.text-link .text-link-disabled').hasClass('ng-hide')
        ).toBe(false);
    });
});
