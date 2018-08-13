describe('component: zemGridIntegration', function() {
    var $componentController;
    var zemGridEndpointService, zemDataSourceService;
    var $ctrl;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function($injector) {
        $componentController = $injector.get('$componentController');
        zemGridEndpointService = $injector.get('zemGridEndpointService');
        zemDataSourceService = $injector.get('zemDataSourceService');

        var locals = {};
        var bindings = {
            options: {},
            level: constants.level.ACCOUNTS,
            breakdown: constants.breakdown.MEDIA_SOURCE,
            entityId: -1,
            selection: {},
            selectionCallback: angular.noop,
        };
        $ctrl = $componentController('zemGridIntegration', locals, bindings);
    }));

    it('should initialize using api', function() {
        spyOn(zemGridEndpointService, 'createMetaData').and.callThrough();
        spyOn(zemGridEndpointService, 'createEndpoint').and.callThrough();
        spyOn(zemDataSourceService, 'createInstance').and.callThrough();
        $ctrl.$onInit();

        expect(zemGridEndpointService.createMetaData).toHaveBeenCalled();
        expect(zemGridEndpointService.createEndpoint).toHaveBeenCalled();
        expect(zemDataSourceService.createInstance).toHaveBeenCalled();

        expect($ctrl.grid).toBeDefined();
        expect($ctrl.grid.options).toBeDefined();
        expect($ctrl.grid.dataSource).toBeDefined();
    });
});
