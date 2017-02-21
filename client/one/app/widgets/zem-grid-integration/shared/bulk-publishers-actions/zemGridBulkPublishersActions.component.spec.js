describe('component: zemGridBulkPublishersActions', function () {
    var $componentController;
    var zemGridConstants;
    var zemGridBulkPublishersActionsService;
    var zemDataFilterService;
    var $ctrl, api;

    beforeEach(module('one'));
    beforeEach(inject(function ($injector) {
        $componentController = $injector.get('$componentController');
        zemGridConstants = $injector.get('zemGridConstants');
        zemGridBulkPublishersActionsService = $injector.get('zemGridBulkPublishersActionsService');
        zemDataFilterService = $injector.get('zemDataFilterService');

        var zemGridMocks = $injector.get('zemGridMocks');
        api = zemGridMocks.createApi(constants.level.CAMPAIGNS, constants.breakdown.AD_GROUP);

        var locals = {};
        var bindings = {api: api};
        $ctrl = $componentController('zemGridBulkPublishersActions', locals, bindings);
    }));

    it('should configure selection options and listen to selection updates', function () {
        spyOn(api, 'onSelectionUpdated');
        spyOn(api, 'setSelectionOptions');
        spyOn(zemGridBulkPublishersActionsService, 'createInstance').and.callThrough();
        $ctrl.$onInit();

        expect(zemGridBulkPublishersActionsService.createInstance).toHaveBeenCalled();
        expect(api.onSelectionUpdated).toHaveBeenCalled();
        expect(api.setSelectionOptions).toHaveBeenCalled();
    });

    it('should enable actions when rows are selected', function () {
        var selection = {
            type: zemGridConstants.gridSelectionFilterType.NONE,
            selected: [{level: 1}]
        };
        api.getSelection = function () { return selection; };
        $ctrl.$onInit();
        expect($ctrl.isEnabled()).toBe(true);
    });

    describe('after init', function () {
        beforeEach(function () {
            $ctrl.$onInit();
        });

        it('should define publisher actions', function () {
            expect($ctrl.blacklistActions).toBeDefined();
            expect($ctrl.blacklistActions.length).toEqual(4);

            expect($ctrl.unlistActions).toBeDefined();
            expect($ctrl.unlistActions.length).toEqual(4);
        });

        it('should execute action using selection', function () {
            var selection = {
                type: zemGridConstants.gridSelectionFilterType.NONE,
                selected: [{
                    level: 1, data: {
                        stats: {
                            'source_id': {value: 1},
                            'domain': {value: 'domain'},
                        }
                    }
                }],
                unselected: [],
                filterAll: false,
                filterId: null,
            };

            api.getSelection = function () { return selection; };
            api.clearSelection = angular.noop;
            var action = $ctrl.unlistActions[0];

            var dateRange = {startDate: moment('2017-01-01'), endDate: moment('2017-01-01')};
            spyOn(zemDataFilterService, 'getDateRange').and.returnValue(dateRange);
            spyOn(api, 'getSelection').and.callThrough();
            spyOn(api, 'clearSelection').and.callThrough();
            spyOn($ctrl.service, 'execute').and.callThrough();

            $ctrl.execute(action.value);

            expect(api.getSelection).toHaveBeenCalled();
            expect($ctrl.service.execute).toHaveBeenCalledWith(action, false);
        });
    });
});
