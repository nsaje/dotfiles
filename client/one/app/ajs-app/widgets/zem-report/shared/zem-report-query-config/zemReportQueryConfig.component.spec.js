describe('component: zemReportQueryConfig', function() {
    var $componentController;
    var $ctrl,
        zemAuthStore,
        zemLocalStorageService,
        zemReportFieldsService,
        gridApi;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function($injector) {
        $componentController = $injector.get('$componentController');
        zemAuthStore = $injector.get('zemAuthStore');
        zemLocalStorageService = $injector.get('zemLocalStorageService');
        zemReportFieldsService = $injector.get('zemReportFieldsService');
        gridApi = $injector
            .get('zemGridMocks')
            .createApi(constants.level.CAMPAIGNS, constants.breakdown.AD_GROUP);

        zemAuthStore.setMockedPermissions([
            'zemauth.can_view_breakdown_by_delivery',
            'zemauth.can_see_managers_in_campaigns_table',
        ]);

        spyOn(gridApi, 'getBreakdown').and.returnValue(['test_breakdown']);
        spyOn(zemReportFieldsService, 'getFields').and.returnValue([]);

        var element = angular.element('<div></div>');
        var locals = {$element: element};
        var bindings = {gridApi: gridApi};
        $ctrl = $componentController('zemReportQueryConfig', locals, bindings);
    }));

    it('unselects selected columns', function() {
        var columns = getSelectedColumns();
        $ctrl.selectedColumns = angular.copy(columns);
        spyOn($ctrl, 'update').and.callFake(function() {});
        $ctrl.toggleColumns(columns, false);

        expect($ctrl.selectedColumns.length).toBe(0);
    });

    it('selects all columns', function() {
        var columns = getSelectedColumns();
        $ctrl.selectedColumns = [];
        spyOn($ctrl, 'update').and.callFake(function() {});
        $ctrl.toggleColumns(angular.copy(columns), true);

        expect($ctrl.selectedColumns.length).toBe(3);
    });

    it('selects one column', function() {
        var columns = getSelectedColumns();
        $ctrl.selectedColumns = angular.copy(columns);
        spyOn($ctrl, 'update').and.callFake(function() {});
        var selectedColumn = ['my selected column'];
        $ctrl.toggleColumns(selectedColumn, true);

        expect($ctrl.selectedColumns.length).toBe(4);
    });

    it('unselects one column', function() {
        var columns = getSelectedColumns();
        $ctrl.selectedColumns = angular.copy(columns);
        spyOn($ctrl, 'update').and.callFake(function() {});
        var selectedColumn = ['my unselected column'];
        $ctrl.toggleColumns(selectedColumn, false);

        expect($ctrl.selectedColumns.length).toBe(3);
    });

    it('sets default csv config', function() {
        spyOn(zemAuthStore, 'getCurrentUser').and.returnValue({
            defaultCsvSeparator: null,
            defaultCsvDecimalSeparator: null,
        });
        spyOn(zemLocalStorageService, 'get').and.returnValue(null);
        $ctrl.$onInit();
        expect($ctrl.config.csvSeparator).toBe(',');
        expect($ctrl.config.csvDecimalSeparator).toBe('.');
    });

    it('sets agency csv config', function() {
        spyOn(zemAuthStore, 'getCurrentUser').and.returnValue({
            defaultCsvSeparator: 'a',
            defaultCsvDecimalSeparator: 'b',
        });
        spyOn(zemLocalStorageService, 'get').and.returnValue(null);
        $ctrl.$onInit();
        expect($ctrl.config.csvSeparator).toBe('a');
        expect($ctrl.config.csvDecimalSeparator).toBe('b');
    });

    it('sets localsettings csv config', function() {
        spyOn(zemAuthStore, 'getCurrentUser').and.returnValue({
            defaultCsvSeparator: 'a',
            defaultCsvDecimalSeparator: 'b',
        });
        spyOn(zemLocalStorageService, 'get').and.callFake(function(key) {
            if (key === 'csvSeparator') {
                return 'c';
            } else if (key === 'csvDecimalSeparator') {
                return 'd';
            }
        });
        $ctrl.$onInit();
        expect($ctrl.config.csvSeparator).toBe('c');
        expect($ctrl.config.csvDecimalSeparator).toBe('d');
    });

    function getSelectedColumns() {
        return ['Agency', 'Managment', 'Costs'];
    }
});
