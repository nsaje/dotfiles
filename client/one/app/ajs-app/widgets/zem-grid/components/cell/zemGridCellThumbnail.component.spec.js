describe('zemGridCellThumbnail', function() {
    var scope, element, $compile;

    var template =
        '<zem-grid-cell-thumbnail data="ctrl.data" column="ctrl.col" row="ctrl.row" grid="ctrl.grid"></zem-grid-cell-thumbnail>'; // eslint-disable-line max-len

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($rootScope, _$compile_) {
        $compile = _$compile_;

        scope = $rootScope.$new();
        scope.ctrl = {};

        element = $compile(template)(scope);
    }));

    it('should set correct thumbnail src', function() {
        scope.ctrl.data = {
            square: 'http://example.com/thumbnail.jpg',
        };
        scope.$digest();

        expect(element.find('img').attr('src')).toEqual(
            'http://example.com/thumbnail.jpg'
        );
    });
});
