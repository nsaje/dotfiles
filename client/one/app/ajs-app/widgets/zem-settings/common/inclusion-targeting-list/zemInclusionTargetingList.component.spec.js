describe('component: zemInclusionTargetingList', function() {
    var $componentController;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($rootScope, _$componentController_) {
        $componentController = _$componentController_;
    }));

    it('should display edit section if editing is enabled by user', function() {
        var bindings = {
            targetings: {
                included: [],
                excluded: [],
            },
        };
        var $ctrl = $componentController(
            'zemInclusionTargetingList',
            {},
            bindings
        );
        expect($ctrl.isTargetingEditSectionVisible()).toBeFalsy();
        $ctrl.enableTargetingEditSection();
        expect($ctrl.isTargetingEditSectionVisible()).toBeTruthy();
    });

    it('should display edit section if some targetings are included', function() {
        var bindings = {
            targetings: {
                included: [{}],
                excluded: [],
            },
        };
        var $ctrl = $componentController(
            'zemInclusionTargetingList',
            {},
            bindings
        );
        expect($ctrl.isTargetingEditSectionVisible()).toBeTruthy();
    });

    it('should display edit section if some targetings are excluded', function() {
        var bindings = {
            targetings: {
                included: [],
                excluded: [{}],
            },
        };
        var $ctrl = $componentController(
            'zemInclusionTargetingList',
            {},
            bindings
        );
        expect($ctrl.isTargetingEditSectionVisible()).toBeTruthy();
    });
});
