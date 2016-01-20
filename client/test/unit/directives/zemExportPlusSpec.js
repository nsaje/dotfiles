'use strict';

describe('zemExportPlus', function () {
    var $scope, isolate, controller;

    beforeEach(module('one'));
    var template = '<zem-export-plus start-date="test" end-date="test" base-url="test" options="test" columns="test" order="test" level="test" export-sources="false"></zem-export-plus>';
    beforeEach(inject(function ($compile, $rootScope) {
        $scope = $rootScope.$new();

        var element = $compile(template)($scope);

        $scope.$digest();
        isolate = element.isolateScope();
    }));

    describe('zemExportPlus', function () {
        it('tests getAdditionalColumns', function () {
            isolate.columns = [
                {field: 'cost', shown: true, checked: true, unselectable: false},
                {field: 'impressions', shown: true, checked: true, unselectable: false}
            ];
            expect(isolate.getAdditionalColumns()).toEqual(['cost', 'impressions']);

            isolate.columns = [
                {field: 'cost', shown: false, checked: true, unselectable: false},
                {field: 'impressions', shown: true, checked: true, unselectable: false}
            ];
            expect(isolate.getAdditionalColumns()).toEqual(['impressions']);

            isolate.columns = [
                {field: 'cost', shown: true, checked: false, unselectable: false},
                {field: 'impressions', shown: true, checked: true, unselectable: false}
            ];
            expect(isolate.getAdditionalColumns()).toEqual(['impressions']);

            isolate.columns = [
                {field: 'cost', shown: false, checked: true, unselectable: false},
                {field: 'impressions', shown: false, checked: true, unselectable: false}
            ];
            expect(isolate.getAdditionalColumns()).toEqual([]);
        });

    });
});
