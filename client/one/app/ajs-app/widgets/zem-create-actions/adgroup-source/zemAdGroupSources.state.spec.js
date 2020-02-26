describe('state: zemAdGroupSourcesStateService', function() {
    var $q;
    var zemAdGroupSourcesStateService, zemAdGroupSourcesEndpoint;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function($injector) {
        $q = $injector.get('$q');
        zemAdGroupSourcesStateService = $injector.get(
            'zemAdGroupSourcesStateService'
        );
        zemAdGroupSourcesEndpoint = $injector.get('zemAdGroupSourcesEndpoint');
    }));

    it('should prepare state object', function() {
        var stateService = zemAdGroupSourcesStateService.getInstance({id: -1});
        expect(stateService.getState()).toEqual({
            sources: [],
            requests: jasmine.any(Object),
        });
    });

    it('should fill the state on initaliation', function() {
        spyOn(zemAdGroupSourcesEndpoint, 'list').and.callThrough();
        var stateService = zemAdGroupSourcesStateService.getInstance({id: -1});
        stateService.initialize();
        expect(zemAdGroupSourcesEndpoint.list).toHaveBeenCalled();
    });

    describe('state service actions', function() {
        var stateService;
        beforeEach(inject(function($injector) {
            stateService = zemAdGroupSourcesStateService.getInstance({id: -1});

            var $httpBackend = $injector.get('$httpBackend');
            $httpBackend.whenGET(/^\/api\/.*\/nav\//).respond(200, {data: {}});

            spyOn(zemAdGroupSourcesEndpoint, 'create').and.callFake(function() {
                return $q.resolve();
            });
            spyOn(zemAdGroupSourcesEndpoint, 'list').and.callFake(function() {
                return $q.resolve({sources: []});
            });
        }));

        it('should use endpoint service for creation', function() {
            stateService.create(1);
            expect(zemAdGroupSourcesEndpoint.create).toHaveBeenCalledWith(
                -1,
                1
            );
        });

        it('should use endpoint for list', function() {
            stateService.list(1);
            expect(zemAdGroupSourcesEndpoint.list).toHaveBeenCalledWith(-1, {
                filteredSources: [],
            });
        });
    });
});
