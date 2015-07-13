'use strict';

describe('zemLocations', function() {
    var $scope, element, isolate;
    var data = [];

    var template = '<zem-locations zem-selected-location-codes="selectedCodes" zem-sources-without-dma-support="noDMAsupport"></zem-locations>';

    beforeEach(module('one'));

    beforeEach(inject(function($compile, $rootScope) {
        $scope = $rootScope.$new();

        $scope.selectedCodes = [];
        $scope.noDMAsupport = undefined;

        element = $compile(template)($scope);

        $scope.$digest();
        isolate = element.isolateScope();
    }));

    var addLocation = function(code) {
        isolate.selectedLocationCode = code;
        isolate.addLocation();
        $scope.$digest();
    };

    it('adds a new location', function() {
        addLocation('US');
        addLocation('GB');
        expect($scope.selectedCodes).toEqual(['US', 'GB']);
    });

    it('removes a location', function() {
        $scope.selectedCodes = ['US', 'GB'];
        $scope.$digest();
        isolate.removeSelectedLocation({code: 'GB'});
        expect($scope.selectedCodes).toEqual(['US']);
    });

    it('can undo when DMA is added and US is already selected', function() {
        $scope.selectedCodes = ['US', 'GB', 'SI'];
        $scope.$digest();
        expect($scope.selectedCodes).toEqual(['US', 'GB', 'SI']);

        addLocation('693');

        expect($scope.selectedCodes).toEqual(['GB', 'SI', '693']);
        expect(isolate.selectedDMASubsetOfUS.length).toBe(1); // undo message ON
        expect(isolate.selectedUS).toBeFalsy();

        isolate.undo();

        $scope.$digest();
        expect($scope.selectedCodes).toEqual(['US', 'GB', 'SI']);
    });

    it('can undo when US is added and DMA\'s are already selected', function() {
        $scope.selectedCodes = ['693', 'GB', 'SI'];
        $scope.$digest();
        expect($scope.selectedCodes).toEqual(['693', 'GB', 'SI']);

        addLocation('US');

        expect($scope.selectedCodes).toEqual(['GB', 'SI', 'US']);
        expect(isolate.selectedDMASubsetOfUS.length).toBe(1); // undo message ON
        expect(isolate.selectedUS).toBeTruthy();

        isolate.undo();

        $scope.$digest();
        expect($scope.selectedCodes).toEqual(['693', 'GB', 'SI']);
    });
});
