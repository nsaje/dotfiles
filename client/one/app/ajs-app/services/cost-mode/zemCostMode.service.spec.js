describe('zemCostModeService', function() {
    var zemCostModeService;
    var onUpdate;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function(_zemCostModeService_) {
        onUpdate = angular.noop;

        zemCostModeService = _zemCostModeService_;
        zemCostModeService.onCostModeUpdate(onUpdate);
    }));

    it('should set correct cost mode', function() {
        zemCostModeService.setCostMode(constants.costMode.ANY);
        expect(zemCostModeService.getCostMode()).toEqual(
            constants.costMode.ANY
        );
    });

    it('should get correct opposite cost mode', function() {
        expect(
            zemCostModeService.getOppositeCostMode(constants.costMode.PUBLIC)
        ).toEqual(constants.costMode.PLATFORM);
        expect(
            zemCostModeService.getOppositeCostMode(constants.costMode.PLATFORM)
        ).toEqual(constants.costMode.PUBLIC);
        expect(
            zemCostModeService.getOppositeCostMode(constants.costMode.ANY)
        ).toEqual(constants.costMode.ANY);
        expect(
            zemCostModeService.getOppositeCostMode(constants.costMode.LEGACY)
        ).toEqual(constants.costMode.LEGACY);
    });

    it('should correctly toggle cost mode', function() {
        zemCostModeService.setCostMode(constants.costMode.PUBLIC);
        zemCostModeService.toggleCostMode();

        expect(zemCostModeService.getCostMode()).toBe(
            constants.costMode.PLATFORM
        );
    });

    it('should correctly return if cost mode is toggleable', function() {
        expect(
            zemCostModeService.isTogglableCostMode(constants.costMode.PUBLIC)
        ).toBe(true);
        expect(
            zemCostModeService.isTogglableCostMode(constants.costMode.PLATFORM)
        ).toBe(true);
        expect(
            zemCostModeService.isTogglableCostMode(constants.costMode.ANY)
        ).toBe(false);
        expect(
            zemCostModeService.isTogglableCostMode(constants.costMode.LEGACY)
        ).toBe(false);
    });
});
