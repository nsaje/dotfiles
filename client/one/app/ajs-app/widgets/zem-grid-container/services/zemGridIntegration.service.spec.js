describe('component: zemGridIntegrationService', function() {
    var $timeout;
    var zemDataSourceService, zemGridEndpointService, zemGridMocks;
    var zemGridIntegrationService, zemDataFilterService, zemSelectionService;

    var defaultEntity;
    var $scope;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function($injector) {
        $timeout = $injector.get('$timeout');

        zemGridMocks = $injector.get('zemGridMocks');
        zemDataSourceService = $injector.get('zemDataSourceService');
        zemGridEndpointService = $injector.get('zemGridEndpointService');
        zemGridIntegrationService = $injector.get('zemGridIntegrationService');
        zemDataFilterService = $injector.get('zemDataFilterService');
        zemSelectionService = $injector.get('zemSelectionService');

        $scope = $injector.get('$rootScope').$new();
        defaultEntity = {
            type: constants.entityType.ACCOUNT,
            id: 'TEST-ACCOUNT-ID',
        };
    }));

    it('should create default grid options on initialization', function() {
        var service = zemGridIntegrationService.createInstance($scope);
        service.initialize();

        expect(service.getGrid().options).toEqual({
            selection: {
                enabled: true,
                filtersEnabled: true,
                levels: [0, 1],
                callbacks: jasmine.any(Object),
            },
        });
    });

    it('should register to DataFilter service on initialization', function() {
        spyOn(zemDataFilterService, 'onDateRangeUpdate').and.callThrough();
        spyOn(zemDataFilterService, 'onDataFilterUpdate').and.callThrough();

        var service = zemGridIntegrationService.createInstance($scope);
        service.initialize();

        expect(zemDataFilterService.onDateRangeUpdate).toHaveBeenCalled();
        expect(zemDataFilterService.onDataFilterUpdate).toHaveBeenCalled();
    });

    it('should register to Selection service after settings grid api', function() {
        spyOn(zemSelectionService, 'onSelectionUpdate').and.callThrough();

        var service = zemGridIntegrationService.createInstance($scope);
        service.initialize();

        expect(zemSelectionService.onSelectionUpdate).not.toHaveBeenCalled();
        service.setGridApi(
            zemGridMocks.createApi(
                constants.level.ACCOUNTS,
                constants.breakdown.CAMPAIGN
            )
        );
        expect(zemSelectionService.onSelectionUpdate).not.toHaveBeenCalled();
        $timeout.flush();
        expect(zemSelectionService.onSelectionUpdate).toHaveBeenCalled();
    });

    it('should create datasource based on the entity and breakdown', function() {
        spyOn(zemDataSourceService, 'createInstance').and.callThrough();
        spyOn(zemGridEndpointService, 'createMetaData').and.callThrough();
        var service = zemGridIntegrationService.createInstance($scope);
        service.initialize();

        expect(service.getGrid().dataSource).not.toBeDefined();

        service.configureDataSource(
            defaultEntity,
            constants.breakdown.CAMPAIGN
        );

        expect(service.getGrid().dataSource).toBeDefined();
        expect(zemDataSourceService.createInstance).toHaveBeenCalled();
        expect(zemGridEndpointService.createMetaData).toHaveBeenCalledWith(
            constants.level.ACCOUNTS,
            defaultEntity.id,
            constants.breakdown.CAMPAIGN
        );
    });

    it('should cache datasource based on the breakdown', function() {
        spyOn(zemDataSourceService, 'createInstance').and.callThrough();
        var service = zemGridIntegrationService.createInstance($scope);
        service.initialize();
        service.configureDataSource(
            defaultEntity,
            constants.breakdown.CAMPAIGN
        );
        expect(zemDataSourceService.createInstance).toHaveBeenCalled();
        var campaignDataSource = service.getGrid().dataSource;

        zemDataSourceService.createInstance.calls.reset();
        service.configureDataSource(
            defaultEntity,
            constants.breakdown.MEDIA_SOURCE
        );
        expect(zemDataSourceService.createInstance).toHaveBeenCalled();
        var mediaDataSource = service.getGrid().dataSource;

        zemDataSourceService.createInstance.calls.reset();
        service.configureDataSource(
            defaultEntity,
            constants.breakdown.CAMPAIGN
        );
        expect(zemDataSourceService.createInstance).not.toHaveBeenCalled();
        expect(service.getGrid().dataSource).toBe(campaignDataSource);

        zemDataSourceService.createInstance.calls.reset();
        service.configureDataSource(
            defaultEntity,
            constants.breakdown.MEDIA_SOURCE
        );
        expect(zemDataSourceService.createInstance).not.toHaveBeenCalled();
        expect(service.getGrid().dataSource).toBe(mediaDataSource);
    });
});
