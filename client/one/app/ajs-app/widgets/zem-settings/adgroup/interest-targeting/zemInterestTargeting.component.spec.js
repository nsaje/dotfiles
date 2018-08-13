describe('component: zemInterestTargeting', function() {
    describe('initialization', function() {
        var $ctrl;

        beforeEach(angular.mock.module('one'));
        beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

        beforeEach(inject(function($rootScope, $componentController) {
            var bindings = {
                entity: {settings: {}},
                errors: {},
                api: {register: angular.noop},
            };
            $ctrl = $componentController('zemInterestTargeting', {}, bindings);
        }));

        it('should initialize without errors', function() {
            $ctrl.$onInit();
        });
    });

    describe('component updates targeting attributes appropriately', function() {
        var $ctrl;

        beforeEach(angular.mock.module('one'));
        beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

        beforeEach(inject(function($rootScope, $componentController) {
            var bindings = {
                entity: {
                    settings: {
                        interestTargeting: ['music', 'cars'],
                        exclusionInterestTargeting: ['hobbies'],
                    },
                },
                errors: {},
                api: {register: angular.noop},
            };
            $ctrl = $componentController('zemInterestTargeting', {}, bindings);
            $ctrl.$onInit();
        }));

        it('should add inclusion interest targeting', function() {
            $ctrl.addIncluded({id: 'education'});
            expect($ctrl.entity.settings.interestTargeting).toEqual([
                'music',
                'cars',
                'education',
            ]);
        });

        it('should add exclusion interest targeting', function() {
            $ctrl.addExcluded({id: 'education'});
            expect($ctrl.entity.settings.exclusionInterestTargeting).toEqual([
                'hobbies',
                'education',
            ]);
        });

        it('should remove inclusion targeting', function() {
            $ctrl.removeTargeting({id: 'music'});
            expect($ctrl.entity.settings.interestTargeting).toEqual(['cars']);
        });

        it('should remove exclusion targeting', function() {
            $ctrl.removeTargeting({id: 'hobbies'});
            expect($ctrl.entity.settings.exclusionInterestTargeting).toEqual(
                []
            );
        });
    });
});
