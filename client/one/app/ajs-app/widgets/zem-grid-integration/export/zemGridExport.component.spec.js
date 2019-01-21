describe('component: zemGridExport', function() {
    var $componentController;
    var zemGridExportOptions;
    var $ctrl, $scope, api;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function($injector) {
        $componentController = $injector.get('$componentController');
        zemGridExportOptions = $injector.get('zemGridExportOptions');

        var zemGridMocks = $injector.get('zemGridMocks');
        api = zemGridMocks.createApi(
            constants.level.ACCOUNTS,
            constants.breakdown.MEDIA_SOURCE
        );

        $scope = {};
        var locals = {$scope: $scope};
        var bindings = {api: api};
        $ctrl = $componentController('zemGridExport', locals, bindings);
    }));

    it('should initialize using api', function() {
        var metaData = api.getMetaData();
        spyOn(zemGridExportOptions, 'getBaseUrl').and.callThrough();
        spyOn(zemGridExportOptions, 'getOptions').and.callThrough();
        spyOn(zemGridExportOptions, 'getDefaultOption').and.callThrough();

        spyOn(api, 'getMetaData').and.callThrough();
        $ctrl.$onInit();

        expect(api.getMetaData).toHaveBeenCalled();
        expect(zemGridExportOptions.getBaseUrl).toHaveBeenCalled();
        expect(zemGridExportOptions.getOptions).toHaveBeenCalled();
        expect(zemGridExportOptions.getDefaultOption).toHaveBeenCalled();

        expect($scope.level).toEqual(metaData.level);
        expect($scope.baseUrl).toBeDefined();
        expect($scope.options).toBeDefined();
        expect($scope.defaultOption).toBeDefined();
        expect($scope.exportSources).toBeDefined();
    });

    it('should provide additional columns (visible, but not permanent)', function() {
        $ctrl.$onInit();

        spyOn(api, 'getVisibleColumns').and.callFake(function() {
            return [
                {data: {field: 'permanent'}, permanent: true},
                {data: {field: 'additional'}, permanent: false},
            ];
        });
        var columns = $scope.getAdditionalColumns();
        expect(api.getVisibleColumns).toHaveBeenCalled();
        expect(columns).toEqual(['additional']);
    });
});
