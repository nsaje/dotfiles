'use strict';

describe('zemSelectionMenu', function() {
    var $scope, element;

    var template = '<zem-selection-menu custom-selection-options="selectionOptions" select-all-callback="selectAllCallback"/>';

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function($compile, $rootScope) {
        $scope = $rootScope.$new();

        $scope.selectAllCallback = function() {};

        $scope.selectionOptions = [{
            type: 'link',
            name: 'This page',
            callback: function() {}
        }, {
            type: 'link-list',
            name: 'Upload batch',
            callback: function() {},
            items: [{id: 1, name: 'batch 1'}]
        }];

        element = $compile(template)($scope);
        $scope.$digest();
    }))

    it('selects all if checkbox is clicked', function() {
        spyOn($scope, 'selectAllCallback');

        element.find('#zem-all-checkbox').trigger('click');
        expect($scope.selectAllCallback).toHaveBeenCalled();
    });

    it('unselects checkbox and calls callback when option is clicked', function() {
        var isolateScope = element.isolateScope();

        spyOn($scope.selectionOptions[0], 'callback');
        isolateScope.selectedAll = true;

        element.find('.link a').trigger('click');

        expect(isolateScope.selectedAll).toBe(false);
        expect($scope.selectionOptions[0].callback).toHaveBeenCalled();
    });

    it('unselects checkbox and calls callback when option item is clicked', function() {
        var isolateScope = element.isolateScope();

        spyOn($scope.selectionOptions[1], 'callback');
        isolateScope.selectedAll = true;

        element.find('.link-list-item a').trigger('click');

        expect(isolateScope.selectedAll).toBe(false);
        expect($scope.selectionOptions[1].callback).toHaveBeenCalled();
    });
});
