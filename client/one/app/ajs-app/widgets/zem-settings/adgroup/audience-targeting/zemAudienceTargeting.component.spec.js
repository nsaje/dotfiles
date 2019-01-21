describe('component: zemAudienceTargeting', function() {
    describe('initialization', function() {
        var $ctrl; // eslint-disable-line no-unused-vars

        beforeEach(angular.mock.module('one'));
        beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
        beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

        beforeEach(inject(function($rootScope, $componentController) {
            var bindings = {
                entity: {settings: {}},
                errors: {},
                api: {register: angular.noop},
            };
            $ctrl = $componentController('zemAudienceTargeting', {}, bindings);
        }));

        it('should initialize without errors', function() {
            $ctrl.$onInit();
        });
    });

    describe('component updates targeting attributes appropriately', function() {
        var $ctrl, targetings; // eslint-disable-line no-unused-vars

        beforeEach(angular.mock.module('one'));
        beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
        beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

        beforeEach(inject(function($rootScope, $componentController) {
            targetings = {
                included: [
                    {
                        type: 'audienceTargeting',
                        section: 'Custom Audiences',
                        id: 11,
                        archived: undefined,
                        name: 'Audience 11 [11]',
                        title: 'Audience "Audience 11" [11]',
                    },
                    {
                        type: 'adGroupTargeting',
                        section: 'Campaign 1',
                        id: 1,
                        archived: undefined,
                        name: 'Ad Group 1 [1]',
                        title: 'Ad group "Ad Group 1" [1]',
                    },
                ],
                excluded: [
                    {
                        type: 'audienceTargeting',
                        section: 'Custom Audiences',
                        id: 22,
                        archived: undefined,
                        name: 'Audience 22 [22]',
                        title: 'Audience "Audience 22" [22]',
                    },
                    {
                        type: 'adGroupTargeting',
                        section: 'Campaign 1',
                        id: 2,
                        archived: undefined,
                        name: 'Ad Group 2 [2]',
                        title: 'Ad group "Ad Group 2" [2]',
                    },
                ],
                notSelected: [
                    {
                        type: 'audienceTargeting',
                        section: 'Custom Audiences',
                        id: 33,
                        archived: undefined,
                        name: 'Audience 33 [33]',
                        title: 'Audience "Audience 33" [33]',
                    },
                    {
                        type: 'adGroupTargeting',
                        section: 'Campaign 2',
                        id: 3,
                        archived: undefined,
                        name: 'Ad Group 3 [3]',
                        title: 'Ad group "Ad Group 3" [3]',
                    },
                ],
            };

            var bindings = {
                entity: {
                    retargetableAdGroups: [
                        {campaignName: 'Campaign 1', id: 1, name: 'Ad Group 1'},
                        {campaignName: 'Campaign 1', id: 2, name: 'Ad Group 2'},
                        {campaignName: 'Campaign 2', id: 3, name: 'Ad Group 3'},
                    ],
                    audiences: [
                        {id: 11, name: 'Audience 11'},
                        {id: 22, name: 'Audience 22'},
                        {id: 33, name: 'Audience 33'},
                    ],
                    settings: {
                        retargetingAdGroups: [1],
                        exclusionRetargetingAdGroups: [2],
                        audienceTargeting: [11],
                        exclusionAudienceTargeting: [22],
                    },
                },
                errors: {},
                api: {register: angular.noop},
            };
            $ctrl = $componentController('zemAudienceTargeting', {}, bindings);
            $ctrl.$onInit();
            $ctrl.$onChanges();
        }));

        it('should set targetings', function() {
            expect($ctrl.targetings).toEqual(targetings);
        });

        it('should add inclusion audience targeting', function() {
            var targeting = {
                type: 'audienceTargeting',
                id: 33,
            };

            $ctrl.addIncluded(targeting);
            expect($ctrl.entity.settings.audienceTargeting).toEqual([11, 33]);
            expect($ctrl.entity.settings.exclusionAudienceTargeting).toEqual([
                22,
            ]);
        });

        it('should add exclusion audience targeting', function() {
            var targeting = {
                type: 'audienceTargeting',
                id: 33,
            };

            $ctrl.addExcluded(targeting);
            expect($ctrl.entity.settings.audienceTargeting).toEqual([11]);
            expect($ctrl.entity.settings.exclusionAudienceTargeting).toEqual([
                22,
                33,
            ]);
        });

        it('should remove inclusion audience targeting', function() {
            var targeting = {
                type: 'audienceTargeting',
                id: 11,
            };

            $ctrl.removeTargeting(targeting);
            expect($ctrl.entity.settings.audienceTargeting).toEqual([]);
            expect($ctrl.entity.settings.exclusionAudienceTargeting).toEqual([
                22,
            ]);
        });

        it('should remove exclusion audience targeting', function() {
            var targeting = {
                type: 'audienceTargeting',
                id: 22,
            };

            $ctrl.removeTargeting(targeting);
            expect($ctrl.entity.settings.audienceTargeting).toEqual([11]);
            expect($ctrl.entity.settings.exclusionAudienceTargeting).toEqual(
                []
            );
        });

        it('should add inclusion ad group targeting', function() {
            var targeting = {
                type: 'adGroupTargeting',
                id: 3,
            };

            $ctrl.addIncluded(targeting);
            expect($ctrl.entity.settings.retargetingAdGroups).toEqual([1, 3]);
            expect($ctrl.entity.settings.exclusionRetargetingAdGroups).toEqual([
                2,
            ]);
        });

        it('should add exclusion ad group targeting', function() {
            var targeting = {
                type: 'adGroupTargeting',
                id: 3,
            };

            $ctrl.addExcluded(targeting);
            expect($ctrl.entity.settings.retargetingAdGroups).toEqual([1]);
            expect($ctrl.entity.settings.exclusionRetargetingAdGroups).toEqual([
                2,
                3,
            ]);
        });

        it('should remove inclusion ad group targeting', function() {
            var targeting = {
                type: 'adGroupTargeting',
                id: 1,
            };

            $ctrl.removeTargeting(targeting);
            expect($ctrl.entity.settings.retargetingAdGroups).toEqual([]);
            expect($ctrl.entity.settings.exclusionRetargetingAdGroups).toEqual([
                2,
            ]);
        });

        it('should remove exclusion ad group targeting', function() {
            var targeting = {
                type: 'adGroupTargeting',
                id: 2,
            };

            $ctrl.removeTargeting(targeting);
            expect($ctrl.entity.settings.retargetingAdGroups).toEqual([1]);
            expect($ctrl.entity.settings.exclusionRetargetingAdGroups).toEqual(
                []
            );
        });
    });
});
