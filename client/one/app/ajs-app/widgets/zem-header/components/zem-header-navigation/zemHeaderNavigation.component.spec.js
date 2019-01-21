describe('component: zemHeaderNavigation', function() {
    var $componentController;
    var hotkeys;
    var ctrl;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(_$componentController_, _hotkeys_) {
        $componentController = _$componentController_;
        hotkeys = _hotkeys_;

        var element = angular.element('<div></div>');
        var locals = {$element: element};
        ctrl = $componentController('zemHeaderNavigation', locals, {});
    }));

    it('should add shortcuts on initialization', function() {
        var addSpy = {add: jasmine.createSpy()};
        spyOn(hotkeys, 'bindTo').and.returnValue(addSpy);
        ctrl.$onInit();
        expect(addSpy.add).toHaveBeenCalledWith({
            combo: 'f',
            callback: jasmine.any(Function),
        });
        expect(addSpy.add).toHaveBeenCalledWith({
            combo: 'enter',
            allowIn: ['INPUT'],
            callback: jasmine.any(Function),
        });
    });
});
