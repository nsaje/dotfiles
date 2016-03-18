/* global describe,beforeEach,module,it,inject,expect */
'use strict';

describe('zemCampaignGoals', function () {
    var $scope, element, isolate;

    beforeEach(module('one'));

    beforeEach(inject(function ($compile, $rootScope) {
        var template = '<zem-campaign-goals account="account" campaign="campaign" goals="campaignGoals" model="campaignGoalsDiff"></zem-campaign-goals>';

        $scope = $rootScope.$new();
        $scope.isPermissionInternal = function () {
            return true;
        };
        $scope.hasPermission = function () {
            return true;
        };
        $scope.campaign = {id: 1};
        $scope.account = {id: 1};
        $scope.goals = [];
        $scope.campaignGoalsDiff = {};

        element = $compile(template)($scope);

        $scope.$digest();
        isolate = element.isolateScope();
    }));

    describe('choosePrimary', function () {
        it('sets first goal to primary', function () {
            isolate.campaignGoals = [{type: 1, id: 1}, {type: 2, id: 2}];

            isolate.choosePrimary();

            expect(isolate.campaignGoals[0].primary).toBe(true);
            expect(isolate.campaignGoals[1].primary).toBeFalsy();
            expect(isolate.model.primary).toBe(1);
        });

        it('sets first goal to primary even if it still has to be added', function () {
            isolate.campaignGoals = [{type: 1}, {type: 2}];
            isolate.model.added = [{type: 1}, {type: 2}];
            isolate.choosePrimary();

            expect(isolate.campaignGoals[0].primary).toBe(true);
            expect(isolate.campaignGoals[1].primary).toBeFalsy();
            expect(isolate.model.primary).toBeFalsy();
            expect(isolate.model.added[0].primary).toBe(true);
        });

    });

    describe('addGoal', function (done) {
        it('opens a modal window', function () {
            isolate.addGoal().result
                .catch(function (error) {
                    expect(error).toBeUndefined();
                })
                .finally(done);
        });
    });
    describe('editGoal', function (done) {
        it('opens a modal window', function () {
            isolate.editGoal().result
                .catch(function (error) {
                    expect(error).toBeUndefined();
                })
                .finally(done);
        });
    });

    describe('setPrimary', function () {
        it ('sets a goal as primary', function () {
            isolate.campaignGoals = [
                {type: 1, primary: true},
                {type: 2, primary: false},
            ];

            isolate.setPrimary(isolate.campaignGoals[1]);
            expect(isolate.campaignGoals[0].primary).toBe(false);
            expect(isolate.campaignGoals[1].primary).toBe(true);
            expect(isolate.model.primary).toBe(null);

            isolate.campaignGoals = [
                {type: 1, primary: true},
                {type: 2, primary: false, id: 10},
            ];

            isolate.setPrimary(isolate.campaignGoals[1]);
            expect(isolate.campaignGoals[0].primary).toBe(false);
            expect(isolate.campaignGoals[1].primary).toBe(true);
            expect(isolate.model.primary).toBe(10);
        });
    });

    describe('deleteGoal', function () {
        it ('removes goal only from model & ui if new', function () {
            isolate.campaignGoals = [
                {type: 1, primary: true},
                {type: 2, primary: false, id: 10},
            ];
            isolate.model.added = [isolate.campaignGoals[0]];

            isolate.deleteGoal(isolate.campaignGoals[0]);
            expect(isolate.model.added.length).toBe(0);
            expect(isolate.campaignGoals.length).toBe(1);
            expect(isolate.campaignGoals[0].id).toBe(10);

        });

        it ('removes goal only from model, ui and db if existing', function () {
            isolate.campaignGoals = [
                {type: 1, primary: true},
                {type: 2, primary: false, id: 10},
            ];
            isolate.model.added = [isolate.campaignGoals[0]];

            isolate.deleteGoal(isolate.campaignGoals[1]);

            expect(isolate.model.added.length).toBe(1);
            expect(isolate.campaignGoals.length).toBe(1);
            expect(isolate.campaignGoals[0].id).toBe(undefined);
            expect(isolate.model.removed[0].id).toBe(10);
        });
    });
});
