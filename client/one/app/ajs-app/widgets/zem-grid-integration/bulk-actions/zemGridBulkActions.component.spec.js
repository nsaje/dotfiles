describe('component: zemGridBulkActions', function() {
    var $injector, $componentController;
    var zemGridConstants, zemGridBulkActionsService;
    var $ctrl, api;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(_$injector_) {
        $injector = _$injector_;
        $componentController = $injector.get('$componentController');
        zemGridBulkActionsService = $injector.get('zemGridBulkActionsService');
        zemGridConstants = $injector.get('zemGridConstants');

        var zemGridMocks = $injector.get('zemGridMocks');
        api = zemGridMocks.createApi(
            constants.level.CAMPAIGNS,
            constants.breakdown.AD_GROUP
        );

        var locals = {};
        var bindings = {api: api};
        $ctrl = $componentController('zemGridBulkActions', locals, bindings);
    }));

    it('should prepare actions on initialization using zemGridBulkAction service', function() {
        spyOn(zemGridBulkActionsService, 'createInstance').and.callThrough();
        var selection = {
            type: zemGridConstants.gridSelectionFilterType.NONE,
            selected: [{level: 0}],
        };
        api.getSelection = function() {
            return selection;
        };
        $ctrl.$onInit();
        expect(zemGridBulkActionsService.createInstance).toHaveBeenCalled();
        expect($ctrl.actions).toBeDefined();
    });

    it('should enable actions when data row (level 1) is selected', function() {
        var selection = {
            type: zemGridConstants.gridSelectionFilterType.NONE,
            selected: [{level: 1, data: {stats: {}}}],
        };
        api.getSelection = function() {
            return selection;
        };
        $ctrl.$onInit();
        expect($ctrl.isEnabled()).toBe(true);
    });

    it('should disable actions when footer (level 0) is selected', function() {
        var selection = {
            type: zemGridConstants.gridSelectionFilterType.NONE,
            selected: [{level: 0}],
        };
        api.getSelection = function() {
            return selection;
        };
        $ctrl.$onInit();
        expect($ctrl.isEnabled()).toBe(false);
    });

    it('should execute action using selection', function() {
        var selection = {
            type: zemGridConstants.gridSelectionFilterType.NONE,
            selected: [{level: 0}],
            unselected: [],
            filterAll: false,
            filterId: null,
        };
        api.getSelection = function() {
            return selection;
        };
        var action = {
            value: 'some action',
            execute: angular.noop,
        };
        spyOn(action, 'execute').and.callFake(
            zemSpecsHelper.getMockedAsyncFunction($injector)
        );
        $ctrl.actions = [action];
        $ctrl.execute(action.value);

        expect(action.execute).toHaveBeenCalled();
    });
});
