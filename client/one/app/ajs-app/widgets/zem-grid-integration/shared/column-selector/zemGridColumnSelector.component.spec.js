describe('component: zemGridColumnSelector', function () {
    var $componentController;
    var $ctrl, api, zemPermissions;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(angular.mock.module('one.mocks.zemPermissions'));

    beforeEach(inject(function ($injector) {
        $componentController = $injector.get('$componentController');
        zemPermissions = $injector.get('zemPermissions');
        zemPermissions.setMockedPermissions([
            'zemauth.can_view_breakdown_by_delivery',
            'zemauth.can_see_managers_in_campaigns_table'
        ]);

        var zemGridMocks = $injector.get('zemGridMocks');
        api = zemGridMocks.createApi(constants.level.ACCOUNTS, constants.breakdown.MEDIA_SOURCE);

        var element = angular.element('<div></div>');
        var locals = {$element: element};
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

    it('should get appropriate costMode columns', function () {
        var columns = [
            {name: 'column1', field: 'c1', visible: true, data: {shown: true, costMode: constants.costMode.PLATFORM}},
            {name: 'column2', field: 'c1', visible: true, data: {shown: true, costMode: constants.costMode.PUBLIC}},
        ];
        var category = {fields: ['c1'], columns: columns};

        api.getCostMode = function () { return constants.costMode.PUBLIC; };
        api.getColumns = function () { return columns; };
        api.getMetaData = function () { return {categories: [category]}; };

        $ctrl.$onInit();

        expect($ctrl.categories[0].columns).toEqual([columns[1]]);
    });
});
