describe('zemRetargeting', function() {
    var $ctrl, targetings;

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
            entityId: 1000,
            retargetableAdGroups: [
                {campaignName: 'Campaign 1', id: 1, name: 'Ad Group 1'},
                {campaignName: 'Campaign 1', id: 2, name: 'Ad Group 2'},
                {campaignName: 'Campaign 2', id: 3, name: 'Ad Group 3'},
            ],
            retargetableAudiences: [
                {id: 11, name: 'Audience 11'},
                {id: 22, name: 'Audience 22'},
                {id: 33, name: 'Audience 33'},
            ],
            includedAdGroups: [1],
            excludedAdGroups: [2],
            includedAudiences: [11],
            excludedAudiences: [22],
            onUpdate: angular.noop,
        };
        $ctrl = $componentController('zemRetargeting', {}, bindings);
        $ctrl.$onChanges({
            entityId: {currentValue: bindings.entityId},
        });
    }));

    it('should set targetings', function() {
        expect($ctrl.targetings).toEqual(targetings);
    });

    it('should add inclusion audience targeting', function() {
        spyOn($ctrl, 'onUpdate');
        var targeting = {
            type: 'audienceTargeting',
            id: 33,
        };

        $ctrl.addIncluded(targeting);
        expect($ctrl.onUpdate).toHaveBeenCalledWith({
            $event: {includedAudiences: [11, 33]},
        });
    });

    it('should add exclusion audience targeting', function() {
        spyOn($ctrl, 'onUpdate');
        var targeting = {
            type: 'audienceTargeting',
            id: 33,
        };

        $ctrl.addExcluded(targeting);
        expect($ctrl.onUpdate).toHaveBeenCalledWith({
            $event: {excludedAudiences: [22, 33]},
        });
    });

    it('should remove inclusion audience targeting', function() {
        spyOn($ctrl, 'onUpdate');
        var targeting = {
            type: 'audienceTargeting',
            id: 11,
        };

        $ctrl.removeTargeting(targeting);
        expect($ctrl.onUpdate).toHaveBeenCalledWith({
            $event: {
                includedAudiences: [],
                excludedAudiences: undefined,
                includedAdGroups: undefined,
                excludedAdGroups: undefined,
            },
        });
    });

    it('should remove exclusion audience targeting', function() {
        spyOn($ctrl, 'onUpdate');
        var targeting = {
            type: 'audienceTargeting',
            id: 22,
        };

        $ctrl.removeTargeting(targeting);
        expect($ctrl.onUpdate).toHaveBeenCalledWith({
            $event: {
                includedAudiences: undefined,
                excludedAudiences: [],
                includedAdGroups: undefined,
                excludedAdGroups: undefined,
            },
        });
    });

    it('should add inclusion ad group targeting', function() {
        spyOn($ctrl, 'onUpdate');
        var targeting = {
            type: 'adGroupTargeting',
            id: 3,
        };

        $ctrl.addIncluded(targeting);
        expect($ctrl.onUpdate).toHaveBeenCalledWith({
            $event: {
                includedAdGroups: [1, 3],
            },
        });
    });

    it('should add exclusion ad group targeting', function() {
        spyOn($ctrl, 'onUpdate');
        var targeting = {
            type: 'adGroupTargeting',
            id: 3,
        };

        $ctrl.addExcluded(targeting);
        expect($ctrl.onUpdate).toHaveBeenCalledWith({
            $event: {
                excludedAdGroups: [2, 3],
            },
        });
    });

    it('should remove inclusion ad group targeting', function() {
        spyOn($ctrl, 'onUpdate');
        var targeting = {
            type: 'adGroupTargeting',
            id: 1,
        };

        $ctrl.removeTargeting(targeting);
        expect($ctrl.onUpdate).toHaveBeenCalledWith({
            $event: {
                includedAudiences: undefined,
                excludedAudiences: undefined,
                includedAdGroups: [],
                excludedAdGroups: undefined,
            },
        });
    });

    it('should remove exclusion ad group targeting', function() {
        spyOn($ctrl, 'onUpdate');
        var targeting = {
            type: 'adGroupTargeting',
            id: 2,
        };

        $ctrl.removeTargeting(targeting);
        expect($ctrl.onUpdate).toHaveBeenCalledWith({
            $event: {
                includedAudiences: undefined,
                excludedAudiences: undefined,
                includedAdGroups: undefined,
                excludedAdGroups: [],
            },
        });
    });
});
