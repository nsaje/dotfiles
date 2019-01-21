describe('zemGridCellSubmissionStatus', function() {
    var scope, element, $compile;

    var template =
        '<zem-grid-cell-submission-status data="ctrl.data" column="ctrl.col" row="ctrl.row" grid="ctrl.grid"></zem-grid-cell-submission-status>'; // eslint-disable-line max-len

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($rootScope, _$compile_) {
        $compile = _$compile_;

        scope = $rootScope.$new();
        scope.ctrl = {};
        scope.ctrl.row = {};
        scope.ctrl.col = {};
        scope.ctrl.col.data = {};
        scope.ctrl.grid = {};

        element = $compile(template)(scope);
    }));

    it('should display 0 if no submissions are available', function() {
        scope.ctrl.data = [];
        scope.$digest();

        expect(element.find('.approved').hasClass('ng-hide')).toBe(true);
        expect(element.find('.non-approved').hasClass('ng-hide')).toBe(true);
        expect(element.find('.no-submission').hasClass('ng-hide')).toBe(false);
    });

    it('should display correct number of approved and non-approved submissions', function() {
        scope.ctrl.data = [
            {
                name: 'Test 1',
                source_state: '',
                status: 2,
                text: 'Approved',
            },
            {
                name: 'Test 2',
                source_state: '',
                status: 2,
                text: 'Approved',
            },
            {
                name: 'Test 3',
                source_state: '',
                status: 2,
                text: 'Approved',
            },
            {
                name: 'Test 4',
                source_state: '',
                status: 1,
                text: 'Approved',
            },
            {
                name: 'Test 5',
                source_state: '',
                status: 1,
                text: 'Approved',
            },
            {
                name: 'Test 6',
                source_state: '',
                status: 3,
                text: 'Approved',
            },
            {
                name: 'Test 7',
                source_state: '',
                status: 3,
                text: 'Approved',
            },
        ];
        scope.$digest();

        expect(
            element
                .find('.approved')
                .text()
                .trim()
        ).toEqual('3');
        expect(
            element
                .find('.non-approved')
                .text()
                .trim()
        ).toEqual('4');
        expect(element.find('.no-submission').hasClass('ng-hide')).toBe(true);
    });
});
