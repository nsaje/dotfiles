/* globals $, describe, inject, beforeEach, module, it, expect */

describe('zemNavSearch', function () {
    var $scope, element, isolate;
    var template = '<zem-nav-search zem-show-archived="showArchived" zem-all-accounts="accounts" zem-can-access-accounts="canAccessAccounts" zem-can-access-campaigns="canAccessCampaigns"></zem-nav-search>';

    beforeEach(module('one'));

    beforeEach(inject(function ($compile, $rootScope) {
        $scope = $rootScope.$new();

        $scope.showArchived = true;
        $scope.canAccessAccounts = true;
        $scope.canAccessCampaigns = true;
        $scope.accounts = [{
            id: 1,
            name: 'test account 1',
            archived: false,
            agency: 'test agency',
            campaigns: [{
                id: 1,
                name: 'test campaign 1',
                archived: false,
                adGroups: [{
                    id: 1,
                    name: 'test ad group 1',
                    archived: false,
                }, {
                    id: 2,
                    name: 'test ad group 2',
                    archived: true,
                }],
            }],
        }, {
            id: 2,
            name: 'test account 2',
            archived: false,
            agency: 'test agency',
            campaigns: [{
                id: 2,
                name: 'test campaign 2',
                archived: false,
                adGroups: [],
            }],
        }];

        element = $compile(template)($scope);

        $scope.$digest();
        isolate = element.isolateScope();
    }));

    it('computes options correctly', function () {
        expect(isolate.accounts).toEqual([{
            id: 'account:1',
            name: 'test account 1',
            archived: false,
            agency: 'test agency',
        }, {
            id: 'account:2',
            name: 'test account 2',
            archived: false,
            agency: 'test agency',
        }]);

        expect(isolate.campaigns).toEqual([{
            id: 'campaign:1',
            name: 'test campaign 1',
            archived: false,
            agency: 'test agency',
        }, {
            id: 'campaign:2',
            name: 'test campaign 2',
            archived: false,
            agency: 'test agency',
        }]);

        expect(isolate.adGroups).toEqual([{
            id: 'adGroup:1',
            name: 'test ad group 1',
            archived: false,
            agency: 'test agency',
        }, {
            id: 'adGroup:2',
            name: 'test ad group 2',
            archived: true,
            agency: 'test agency',
        }]);
    });

    it('renders data-agency attribute in options', function () {
        var options = element.find('optgroup option').toArray();

        expect(options.length).toEqual(6);

        options.every(function (option) {
            expect(option.dataset.agency).toEqual('test agency');
        });
    });

    describe('matcher function', function () {
        it('matches option correctly', function () {
            var matches;
            var option = $(element.find('optgroup option')[0]);

            expect(option.text()).toEqual('test account 1');
            expect(option.data('agency')).toEqual('test agency');

            matches = isolate.navSelectorOptions.matcher('account 1', option.text(), option);
            expect(matches).toBe(true);

            matches = isolate.navSelectorOptions.matcher('account 2', option.text(), option);
            expect(matches).toBe(false);

            matches = isolate.navSelectorOptions.matcher('agency', option.text(), option);
            expect(matches).toBe(true);

            matches = isolate.navSelectorOptions.matcher('gen', option.text(), option);
            expect(matches).toBe(true);

            matches = isolate.navSelectorOptions.matcher('nothing', option.text(), option);
            expect(matches).toBe(false);

            matches = isolate.navSelectorOptions.matcher('account agency', option.text(), option);
            expect(matches).toBe(true);
        });
    });
});
