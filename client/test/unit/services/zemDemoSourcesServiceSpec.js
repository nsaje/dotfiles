'use strict';

describe('zemDemoSourcesService', function() {
    var $q, $rootScope, $httpBackend, cache, sources, defaults;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));
    
    beforeEach(inject(function(_$q_, _$rootScope_, _$window_, _$httpBackend_, _zemDemoCacheService_, _zemDemoSourcesService_, _demoDefaults_) {
        sources = _zemDemoSourcesService_;
        defaults = _demoDefaults_;
        cache = _zemDemoCacheService_;
        $q = _$q_;
        $rootScope = _$rootScope_;
        $httpBackend = _$httpBackend_;

        _$window_.demoActions = {
            refreshAdGroupSourcesTable: function () {}
        };

        sources.setApi(function (adGroup) {
            var deferred = $q.defer(),
                table = defaults.emptyTable();
            deferred.resolve(table);
            return deferred.promise;
        });
    }));

    afterEach(function() {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('refresh sources list', function () {
        sources.refresh(1).then(function (data) {
            expect(data).toBe(true);
        });
        sources.refresh(1).then(function (data) {
            expect(data).toBe(false);
        });
        $rootScope.$apply();
    });

    it('add and remove a source', function () {
        var sourcesCacheId = '/api/ad_groups/1/sources/';
        cache.set('/api/ad_groups/1/sources/', {
            sources: [{id: 1, name: "Source 1"}, {id: 2, name: "Source 2"}]
        });
        
        expect(sources.get(1, 1)).not.toBeDefined();
        sources.create(1, { id: 1, name: "Source 1" });
        expect(JSON.stringify(cache.get(sourcesCacheId).sources)).toBe(JSON.stringify(
            [{id: 2, name: "Source 2"}]
        ));

        expect(sources.applyToSourcesTable(1, defaults.emptyTable()).rows[0].id).toBe(1);

        expect(sources.get(1, 1).id).toBe(1);
        expect(sources.get(1, 1)._demo_new).toBe(true);
        expect(sources.get(1, 1).status).toBe('Active');

        expect(JSON.stringify(sources.getForAd(1, 
            { submission_status: ['bla'] }
        ))).toBe(
            JSON.stringify({ submission_status: [
                { status: 2, name: 'Source 1', text: 'Approved / Enabled' }
            ] })
        );

        sources.add(1, 2, { field1: 'value' });
        sources.add(1, 2, { field2: 'value' });
        expect(JSON.stringify(sources.get(1, 2))).toBe(JSON.stringify({
            field1: 'value',
            field2: 'value'
        }));
        
        sources.remove(1, 1);
        expect(sources.get(1, 1)).not.toBeDefined();

        
    });
});
