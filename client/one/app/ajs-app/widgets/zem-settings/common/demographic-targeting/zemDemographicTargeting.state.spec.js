describe('state: zemDemographicTargetingStateService', function() {
    var zemDemographicTargetingStateService;
    var zemDemographicTaxonomyService;
    var $q;

    var expressionEditable = {
        and: [
            {or: [{category: 'bluekai: 123'}, {category: 'bluekai: 234'}]},
            {or: [{category: 'bluekai: 345'}]},
            {not: [{or: [{category: 'bluekai: 432'}]}]},
        ],
    };
    var expressionNonEditable = {
        and: [
            {
                or: [
                    {category: 'bluekai: 123'},
                    {AND: [{category: 'bluekai: 234'}]},
                ],
            },
            {not: [{or: [{category: 'bluekai: 432'}]}]},
        ],
    };

    var entity = {
        settings: {
            bluekaiTargeting: expressionEditable,
        },
    };

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function($injector) {
        zemDemographicTargetingStateService = $injector.get(
            'zemDemographicTargetingStateService'
        );
        zemDemographicTaxonomyService = $injector.get(
            'zemDemographicTaxonomyService'
        );
        $q = $injector.get('$q');

        spyOn(zemDemographicTaxonomyService, 'getTaxonomy').and.callFake(
            function() {
                return $q.resolve({
                    name: 'root',
                    childNodes: [],
                });
            }
        );

        spyOn(zemDemographicTaxonomyService, 'getNodeById').and.callFake(
            function() {
                return {
                    name: 'Test',
                };
            }
        );
    }));

    it('should prepare state object', function() {
        var stateService = zemDemographicTargetingStateService.createInstance({
            settings: {
                bluekaiTargeting: expressionNonEditable,
            },
        });
        expect(stateService.getState()).toEqual({
            expressionTree: null,
            info: null,
            editable: false,
        });
    });

    it('should load the state on initalization', function() {
        var stateService = zemDemographicTargetingStateService.createInstance(
            entity
        );
        stateService.initialize();
        expect(stateService.getState()).toEqual({
            expressionTree: jasmine.any(Object),
            info: jasmine.any(Object),
            editable: jasmine.any(Boolean),
        });
    });

    it('should allow editing on predefined structure', function() {
        var stateService = zemDemographicTargetingStateService.createInstance(
            entity
        );

        stateService.initialize();
        expect(stateService.getState().editable).toBe(true);
    });

    it('should not allow editing on complex nested structures', function() {
        var stateService = zemDemographicTargetingStateService.createInstance({
            settings: {
                bluekaiTargeting: expressionNonEditable,
            },
        });

        stateService.initialize();
        expect(stateService.getState().editable).toBe(false);
    });
});
