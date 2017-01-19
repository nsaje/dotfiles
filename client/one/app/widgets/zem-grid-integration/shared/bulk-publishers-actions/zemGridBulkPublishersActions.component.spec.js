describe('component: zemGridBulkPublishersActions', function () {
    var $componentController;
    var zemGridConstants;
    var $ctrl, api;

    beforeEach(module('one'));
    beforeEach(inject(function ($injector) {
        $componentController = $injector.get('$componentController');
        zemGridConstants = $injector.get('zemGridConstants');

        var zemGridMocks = $injector.get('zemGridMocks');
        api = zemGridMocks.createApi(constants.level.CAMPAIGNS, constants.breakdown.AD_GROUP);

        var locals = {};
        var bindings = {api: api};
        $ctrl = $componentController('zemGridBulkPublishersActions', locals, bindings);
    }));

    it('should configure selection options and listen to selection updates', function () {
        spyOn(api, 'onSelectionUpdated');
        spyOn(api, 'setSelectionOptions');
        $ctrl.$onInit();

        expect(api.onSelectionUpdated).toHaveBeenCalled();
        expect(api.setSelectionOptions).toHaveBeenCalled();
    });

    it('should define publisher actions', function () {
        expect($ctrl.publisherBlacklistActions).toBeDefined();
        expect($ctrl.publisherBlacklistActions.length).toEqual(4);

        expect($ctrl.publisherEnableActions).toBeDefined();
        expect($ctrl.publisherEnableActions.length).toEqual(4);
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

    it('should execute action using selection', function () {
        var selection = {
            type: zemGridConstants.gridSelectionFilterType.NONE,
            selected: [{
                level: 0, data: {
                    stats: {
                        'source_id': {value: 1},
                        'external_id': {value: 2},
                        'domain': {value: 'domain'},
                        'exchange': {value: 'exchange'},
                    }
                }
            }],
            unselected: [],
            filterAll: false,
            filterId: null,
        };

        api.getSelection = function () { return selection; };
        api.clearSelection = angular.noop;
        var action = $ctrl.publisherEnableActions[0];

        spyOn(api, 'getSelection').and.callThrough();
        spyOn(api, 'clearSelection').and.callThrough();
        spyOn(action, 'execute');

        $ctrl.execute(action.value);

        expect(api.getSelection).toHaveBeenCalled();
        expect(api.clearSelection).toHaveBeenCalled();
        expect(action.execute).toHaveBeenCalled();
        expect(action.execute).toHaveBeenCalledWith({
            id: -1,
            selectedPublishers: [{
                'source_id': 1,
                'external_id': 2,
                'domain': 'domain',
                'exchange': 'exchange',
            }],
            unselectedPublishers: [],
            filterAll: false
        });
    });

});
