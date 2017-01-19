describe('component: zemGridColumnSelector', function () {
    var $componentController;
    var $ctrl, api;

    beforeEach(module('one', function ($provide) {
        zemSpecsHelper.provideMockedPermissionsService($provide);
    }));
    beforeEach(inject(function ($injector) {
        $componentController = $injector.get('$componentController');

        var zemGridMocks = $injector.get('zemGridMocks');
        api = zemGridMocks.createApi (constants.level.ACCOUNTS, constants.breakdown.MEDIA_SOURCE);

        var locals = {};
        var bindings = {api: api};
        $ctrl = $componentController('zemGridColumnSelector', locals, bindings);
    }));

    it('should initialize categories using api', function () {
        spyOn(api, 'getMetaData').and.callThrough();
        spyOn(api, 'getColumns').and.callThrough();
        spyOn(api, 'onColumnsUpdated').and.callThrough();

        $ctrl.$onInit();

        expect(api.getMetaData).toHaveBeenCalled();
        expect(api.getColumns).toHaveBeenCalled();
        expect(api.onColumnsUpdated).toHaveBeenCalled();

        expect($ctrl.categories).toBeDefined();
        expect($ctrl.categories.length).toBe(4);
    });

    it('should configure visible columns through api', function () {
        var column = {name: 'column', visible: true};

        spyOn(api, 'setVisibleColumns').and.callThrough();
        $ctrl.columnChecked(column);
        expect(api.setVisibleColumns).toHaveBeenCalled();
        expect(api.setVisibleColumns).toHaveBeenCalledWith(column, true);

        api.setVisibleColumns.calls.reset();
        column.visible = false;
        $ctrl.columnChecked(column);
        expect(api.setVisibleColumns).toHaveBeenCalled();
        expect(api.setVisibleColumns).toHaveBeenCalledWith(column, false);
    });
});
