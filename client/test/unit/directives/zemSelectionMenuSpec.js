'use strict';

describe('zemSelectionMenu', function() {
    var $scope, element;

    var template = '<zem-selection-menu config="config"/>';

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function($compile, $rootScope) {
        $scope = $rootScope.$new();

        var selectAllCallback = function() {};
        var selectionOptions = [{
            type: 'link',
            name: 'This page',
            callback: function() {}
        }, {
            type: 'link-list',
            name: 'Upload batch',
            callback: function() {},
            items: [{id: 1, name: 'batch 1'}]
        }];

        $scope.config = {
            selectAllCallback: selectAllCallback,
            selectionOptions: selectionOptions,
            partialSelection: false
        };

        element = $compile(template)($scope);
        $scope.$digest();
    }));

    it('selects all if checkbox is clicked', function() {
        spyOn($scope.config, 'selectAllCallback');

        element.find('#zem-all-checkbox').trigger('click');
        expect($scope.config.selectAllCallback).toHaveBeenCalled();
    });

    it('unselects checkbox and calls callback when option is clicked', function() {
        var isolateScope = element.isolateScope();

        spyOn($scope.config.selectionOptions[0], 'callback');
        isolateScope.selectedAll = true;

        element.find('.link div').trigger('click');

        expect(isolateScope.selectedAll).toBe(false);
        expect($scope.config.selectionOptions[0].callback).toHaveBeenCalled();
    });

    it('unselects checkbox and calls callback when option item is clicked', function() {
        var isolateScope = element.isolateScope();

        spyOn($scope.config.selectionOptions[1], 'callback');
        isolateScope.selectedAll = true;

        element.find('.link-list-item div').trigger('click');

        expect(isolateScope.selectedAll).toBe(false);
        expect($scope.config.selectionOptions[1].callback).toHaveBeenCalled();
    });

    it('shows indeterminate checkbox when partialSelection', function() {
        var selectAllCheckbox = element.find('#zem-all-checkbox')[0];

        $scope.config.partialSelection = true;
        $scope.$digest();

        expect(selectAllCheckbox.indeterminate).toBe(true);
    });
});
