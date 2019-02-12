describe('component: zemInterestTargeting', function() {
    var $ctrl;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($componentController) {
        var bindings = {
            includedInterests: ['music', 'cars'],
            excludedInterests: ['hobbies'],
            includedInterestsErrors: [],
            excludedInterestsErrors: [],
            onUpdate: angular.noop,
        };
        $ctrl = $componentController('zemInterestTargeting', {}, bindings);
    }));

    it('should add inclusion interest targeting', function() {
        spyOn($ctrl, 'onUpdate');
        $ctrl.addIncluded({id: 'education'});
        expect($ctrl.onUpdate).toHaveBeenCalledWith({
            $event: {includedInterests: ['music', 'cars', 'education']},
        });
    });

    it('should add exclusion interest targeting', function() {
        spyOn($ctrl, 'onUpdate');
        $ctrl.addExcluded({id: 'education'});
        expect($ctrl.onUpdate).toHaveBeenCalledWith({
            $event: {excludedInterests: ['hobbies', 'education']},
        });
    });

    it('should remove inclusion targeting', function() {
        spyOn($ctrl, 'onUpdate');
        $ctrl.removeTargeting({id: 'music'});
        expect($ctrl.onUpdate).toHaveBeenCalledWith({
            $event: {includedInterests: ['cars'], excludedInterests: undefined},
        });
    });

    it('should remove exclusion targeting', function() {
        spyOn($ctrl, 'onUpdate');
        $ctrl.removeTargeting({id: 'hobbies'});
        expect($ctrl.onUpdate).toHaveBeenCalledWith({
            $event: {includedInterests: undefined, excludedInterests: []},
        });
    });
});
