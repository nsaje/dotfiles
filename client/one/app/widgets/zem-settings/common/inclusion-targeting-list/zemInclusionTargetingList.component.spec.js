describe('component: zemInclusionTargetingList', function () {
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
            $ctrl = $componentController('zemInclusionTargetingList', {}, bindings);
        }));

        it('should initialize without errors', function () {
            $ctrl.$onInit();
            expect($ctrl.notSelected).not.toBeDefined();
            expect($ctrl.included).not.toBeDefined();
            expect($ctrl.excluded).not.toBeDefined();
        });
    });

    describe('targeting updates', function () {
        var $ctrl, targeting; // eslint-disable-line no-unused-vars

        beforeEach(module('one'));
        beforeEach(module('one.mocks.zemInitializationService'));

        beforeEach(inject(function ($rootScope, $componentController) {
            targeting = [
                {id: 1, included: false, excluded: false, section: 'a'},
                {id: 2, included: false, excluded: true, section: 'b'},
                {id: 3, included: true, excluded: false, section: 'c'},
            ];

            var bindings = {
                texts: {},
                targetings: targeting,
                addTargeting: angular.noop,
                removeTargeting: angular.noop,
            };
            $ctrl = $componentController('zemInclusionTargetingList', {}, bindings);
            $ctrl.$onInit();
        }));

        it('should set selected targetings correctly', function () {
            expect($ctrl.notSelected).toEqual([targeting[0]]);
            expect($ctrl.excluded).toEqual({b: [targeting[1]]});
            expect($ctrl.included).toEqual({c: [targeting[2]]});
        });

        it('should add inclusion targeting', function () {
            $ctrl.addIncluded(targeting[0]);

            expect($ctrl.notSelected).toEqual([]);
            expect($ctrl.excluded).toEqual({b: [targeting[1]]});
            expect($ctrl.included).toEqual({a: [targeting[0]], c: [targeting[2]]});
        });

        it('should add exclusion targeting', function () {
            $ctrl.addExcluded(targeting[0]);

            expect($ctrl.notSelected).toEqual([]);
            expect($ctrl.excluded).toEqual({a: [targeting[0]], b: [targeting[1]]});
            expect($ctrl.included).toEqual({c: [targeting[2]]});
        });

        it('should remove inclusion targeting', function () {
            $ctrl.remove(targeting[2]);

            expect($ctrl.notSelected).toContain(targeting[2]);
            expect($ctrl.excluded).toEqual({b: [targeting[1]]});
            expect($ctrl.included).not.toBeDefined();
        });

        it('should remove exclusion targeting', function () {
            $ctrl.remove(targeting[1]);

            expect($ctrl.notSelected).toContain(targeting[1]);
            expect($ctrl.excluded).not.toBeDefined();
            expect($ctrl.included).toEqual({c: [targeting[2]]});
        });
    });

});
