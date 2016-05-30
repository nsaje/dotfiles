/* global $,module,beforeEach,it,describe,expect,inject */
'use strict';

describe('zemContentInsights', function () {
    var $scope, element, isolate;
    var data = [];

    var template = '<zem-content-insights summary="contentInsights.summary" metric="contentInsights.metric" best-performer-rows="contentInsights.bestPerformerRows" worst-performer-rows="contentInsights.worstPerformerRows"><div class="insights-container"></div></zem-content-insights>'; // eslint-disable-line max-len

    beforeEach(module('one'));

    beforeEach(inject(function ($compile, $rootScope, $timeout, $httpBackend) {
        $scope = $rootScope.$new();
        $scope.contentInsights = {
            summary: 'title',
            metric: 'ctr',
            bestPerformerRows: [{
                summary: 'Best content ad',
                metric: '90%',
            }],
            worstPerformerRows: [{
                summary: 'Worst content ad',
                metric: '1%',
            }],
        };
        $scope.isPermissionInternal = function () {
            return true;
        };
        $scope.hasPermission = function () {
            return true;
        };
        $httpBackend.when('GET', '/api/users/current/').respond({});
        $httpBackend.when('GET', '/api/all_accounts/nav/').respond({});

        $('.insights-container').css('width', '1000px');

        element = $compile(template)($scope);

        $scope.$digest();
        isolate = element.isolateScope();

        isolate.$digest();
        $timeout.flush();
    }));

    describe('it works', function () {
        it('toggles correctly', function () {
            expect(isolate.expanded).toEqual(false);
            expect(isolate.collapsedDataState).toEqual('best-performers');
            expect(isolate.collapsedRows).toEqual([{
                summary: 'Best content ad',
                metric: '90%',
            }]);

            isolate.showWorstPerformersCollapsed();
            expect(isolate.collapsedDataState).toEqual('worst-performers');
            expect(isolate.collapsedRows).toEqual([{
                summary: 'Worst content ad',
                metric: '1%',
            }]);

            isolate.showBestPerformersCollapsed();
            expect(isolate.collapsedDataState).toEqual('best-performers');
            expect(isolate.collapsedRows).toEqual([{
                summary: 'Best content ad',
                metric: '90%',
            }]);
        });

        it('binds best performers correctly', function () {
            expect(isolate.expanded).toEqual(false);
            expect(isolate.collapsedDataState).toEqual('best-performers');
            expect(isolate.collapsedRows).toEqual([{
                summary: 'Best content ad',
                metric: '90%',
            }]);

            isolate.bestPerformerRows = [];
            isolate.$digest();

            expect(isolate.collapsedRows).toEqual([]);
        });

        it('binds worst performers correctly', function () {
            expect(isolate.expanded).toEqual(false);
            isolate.showWorstPerformersCollapsed();

            expect(isolate.collapsedDataState).toEqual('worst-performers');
            expect(isolate.collapsedRows).toEqual([{
                summary: 'Worst content ad',
                metric: '1%',
            }]);

            isolate.worstPerformerRows = []
            isolate.$digest();

            expect(isolate.collapsedRows).toEqual([]);
        });
    });
});
