describe('component: zemGridBreakdownSelector', function () {
    var $componentController;
    var $ctrl, api;

    beforeEach(module('one'));
    beforeEach(inject(function ($injector) {
        $componentController = $injector.get('$componentController');

        var zemGridMocks = $injector.get('zemGridMocks');
        api = zemGridMocks.createApi(constants.level.ACCOUNTS, constants.breakdown.MEDIA_SOURCE);

        var locals = {};
        var bindings = {api: api};
        $ctrl = $componentController('zemGridBreakdownSelector', locals, bindings);
    }));

    it('should initialize breakdownGroups using api', function () {
        spyOn(api, 'getMetaData').and.callThrough();
        $ctrl.$onInit();
        expect(api.getMetaData).toHaveBeenCalled();
        expect($ctrl.breakdownGroups).toEqual([jasmine.any(Object), jasmine.any(Object), jasmine.any(Object)]);
    });

    it('should apply correct breakdown using api', function () {
        spyOn(api, 'setBreakdown');
        $ctrl.$onInit();

        var group = $ctrl.breakdownGroups[1];
        var breakdown = group.breakdowns[1];
        breakdown.checked = true;
        $ctrl.onChecked(group, breakdown);

        var expectedBreakdown = [];
        expectedBreakdown.push(api.getMetaData().breakdownGroups.base.breakdowns[0]);
        expectedBreakdown.push(breakdown);

        expect(api.setBreakdown).toHaveBeenCalled();
        expect(api.setBreakdown).toHaveBeenCalledWith(expectedBreakdown, true);
    });
});
