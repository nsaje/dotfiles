describe('component: zemInclusionTargetingListLegacy', function () {
    describe('initialization', function () {
        var $ctrl; // eslint-disable-line no-unused-vars

        beforeEach(module('one'));
        beforeEach(module('one.mocks.zemInitializationService'));

        beforeEach(inject(function ($rootScope, $componentController) {
            var bindings = {
                texts: {},
                targetings: [],
                addTargeting: angular.noop,
                removeTargeting: angular.noop,
            };
            $ctrl = $componentController('zemInclusionTargetingListLegacy', {}, bindings);
        }));

        it('should initialize without errors', function () {
            $ctrl.$onInit();
            expect($ctrl.notSelected).toEqual([]);
            expect($ctrl.included).toEqual([]);
            expect($ctrl.excluded).toEqual([]);
        });
    });

    describe('targeting updates', function () {
        var $ctrl, targeting; // eslint-disable-line no-unused-vars

        beforeEach(module('one'));
        beforeEach(module('one.mocks.zemInitializationService'));

        beforeEach(inject(function ($rootScope, $componentController) {
            targeting = [
                {id: 1, included: false, excluded: false},
                {id: 2, included: false, excluded: true},
                {id: 3, included: true, excluded: false},
            ];

            var bindings = {
                texts: {},
                targetings: targeting,
                addTargeting: angular.noop,
                removeTargeting: angular.noop,
            };
            $ctrl = $componentController('zemInclusionTargetingListLegacy', {}, bindings);
            $ctrl.$onInit();
        }));

        it('should set selected targetings correctly', function () {
            expect($ctrl.notSelected).toEqual([targeting[0]]);
            expect($ctrl.included).toEqual([targeting[2]]);
            expect($ctrl.excluded).toEqual([targeting[1]]);
        });

        it('should add inclusion targeting', function () {
            $ctrl.addIncluded(targeting[0]);

            expect($ctrl.notSelected).toEqual([]);
            expect($ctrl.included).toContain(targeting[0]);
            expect($ctrl.excluded).toEqual([targeting[1]]);
        });

        it('should add exclusion targeting', function () {
            $ctrl.addExcluded(targeting[0]);

            expect($ctrl.notSelected).toEqual([]);
            expect($ctrl.included).toEqual([targeting[2]]);
            expect($ctrl.excluded).toContain(targeting[0]);

        });

        it('should remove inclusion targeting', function () {
            $ctrl.remove(targeting[2]);

            expect($ctrl.notSelected).toContain(targeting[2]);
            expect($ctrl.included).toEqual([]);
            expect($ctrl.excluded).toEqual([targeting[1]]);
        });

        it('should remove exclusion targeting', function () {
            $ctrl.remove(targeting[1]);

            expect($ctrl.notSelected).toContain(targeting[1]);
            expect($ctrl.included).toEqual([targeting[2]]);
            expect($ctrl.excluded).toEqual([]);
        });
    });

});
