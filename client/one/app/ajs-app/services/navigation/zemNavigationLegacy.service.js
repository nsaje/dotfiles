angular.module('one.services').factory('zemNavigationService', function ($rootScope, $q, zemNavigationLegacyEndpoint) { // eslint-disable-line max-len

    var postoponedUpdates = {
        accounts: [],
        campaigns: [],
        adGroups: []
    };

    var accounts = [];
    var accountsAccess;

    function findAccountInNavTree (id) {
        var strId = id.toString();

        for (var i = 0; i < accounts.length; i++) {
            if (accounts[i].id.toString() === strId) {
                return {
                    account: accounts[i],
                };
            }
        }
        return undefined;
    }

    function findCampaignInNavTree (id) {
        var strId = id.toString();
        for (var i = 0; i < accounts.length; i++) {
            for (var j = 0; j < accounts[i].campaigns.length; j++) {
                if (accounts[i].campaigns[j].id.toString() === strId) {
                    return {
                        account: accounts[i],
                        campaign: accounts[i].campaigns[j],
                    };
                }
            }
        }
        return undefined;
    }

    function findAdGroupInNavTree (id) {
        var strId = id.toString();
        for (var i = 0; i < accounts.length; i++) {
            for (var j = 0; j < accounts[i].campaigns.length; j++) {
                for (var k = 0; k < accounts[i].campaigns[j].adGroups.length; k++) {
                    if (accounts[i].campaigns[j].adGroups[k].id.toString() === strId) {
                        return {
                            account: accounts[i],
                            campaign: accounts[i].campaigns[j],
                            adGroup: accounts[i].campaigns[j].adGroups[k],
                        };
                    }
                }
            }
        }
        return undefined;
    }

    function loadData (id, apiFunc, searchCacheFunc) {
        // Loads data from cache or calls api if data is not in cache

        if (accounts.length === 0) {
            return apiFunc(id).then(function (data) {

                // if in the meantime data arrived use that one
                // and discard fetched data
                if (accounts.length !== 0) {
                    return searchCacheFunc(id);
                }

                return data;
            });
        }

        // simulate api call - return a promise, but resolve it
        // beforehand just to preserve the api behaviour
        var deferred = $q.defer();

        var data = searchCacheFunc(id);

        deferred.resolve(data);

        return deferred.promise;
    }

    function getAccount (id) {
        return loadData(
            id,
            zemNavigationLegacyEndpoint.getAccount,
            findAccountInNavTree
        );
    }

    function getCampaign (id) {
        return loadData(
            id,
            zemNavigationLegacyEndpoint.getCampaign,
            findCampaignInNavTree
        );
    }

    function getAdGroup (id) {
        return loadData(
            id,
            zemNavigationLegacyEndpoint.getAdGroup,
            findAdGroupInNavTree
        );
    }

    function getAccountsAccess () {
        var deferred = $q.defer();

        if (accountsAccess) {
            deferred.resolve(accountsAccess);
        } else {
            zemNavigationLegacyEndpoint.getAccountsAccess()
                .then(function (data) {
                    accountsAccess = data;
                    deferred.resolve(accountsAccess);
                });
        }

        return deferred.promise;
    }

    function updateModel (model, dataObjOrFunc) {
        // updates a model with provided function or replaces key-values pairs in it
        // if object is provided
        if (typeof dataObjOrFunc === 'function') {
            dataObjOrFunc(model);
        } else {
            Object.keys(dataObjOrFunc).forEach(function (key) {
                model[key] = dataObjOrFunc[key];
            });
        }
    }

    function notifyCacheUpdate () {
        $rootScope.$emit('navigation-updated');
    }

    function notifyAdGroupReloading (id, reloading) {
        $rootScope.$emit('navigation-adgroup-loading-' + id);
        var adGroupCached = findAdGroupInNavTree(id);
        if (adGroupCached) {
            updateModel(adGroupCached.adGroup, {
                reloading: reloading,
            });
        }
    }

    function updateAllAccountsCache (data) {
        Object.keys(data).forEach(function (key) {
            accounts[key] = data[key];
        });
        notifyCacheUpdate();
    }

    function updateAccountCache (id, data) {
        var fromCache = findAccountInNavTree(id);
        updateModel(fromCache.account, data);
        notifyCacheUpdate();
    }

    function updateCampaignCache (id, data) {
        var fromCache = findCampaignInNavTree(id);
        updateModel(fromCache.campaign, data);
        notifyCacheUpdate();
    }

    function updateAdGroupCache (id, data) {
        var fromCache = findAdGroupInNavTree(id);
        updateModel(fromCache.adGroup, data);
        notifyCacheUpdate();
    }

    function addAccountToCache (data) {
        accounts.push(data);
        notifyCacheUpdate();
    }

    function addCampaignToCache (id, data) {
        var fromCache = findAccountInNavTree(id);
        fromCache.account.campaigns.push(data);
        notifyCacheUpdate();
    }

    function addAdGroupToCache (id, data) {
        var fromCache = findCampaignInNavTree(id);
        fromCache.campaign.adGroups.push(data);
        notifyCacheUpdate();
    }

    function reload () {
        $rootScope.$emit('navigation-loading', true);
        return zemNavigationLegacyEndpoint.list().then(function (data) {
            accounts = data;
            updatePostponedData();
            notifyCacheUpdate();
            return data;
        }).finally(function () {
            $rootScope.$emit('navigation-loading', false);
        });
    }

    function postponeDataUpdate (data) {
        if (data.account) postoponedUpdates.accounts.push(data.account);
        if (data.campaign) postoponedUpdates.campaigns.push(data.campaign);
        if (data.adGroup) postoponedUpdates.adGroups.push(data.adGroup);
    }

    function updatePostponedData () {
        postoponedUpdates.accounts.forEach(function (account) {
            updateModel(findAccountInNavTree(account.id).account, account);
        });
        postoponedUpdates.campaigns.forEach(function (campaign) {
            updateModel(findCampaignInNavTree(campaign.id).campaign, campaign);
        });
        postoponedUpdates.adGroups.forEach(function (adGroup) {
            updateModel(findAdGroupInNavTree(adGroup.id).adGroup, adGroup);
        });

        postoponedUpdates.accounts = [];
        postoponedUpdates.campaigns = [];
        postoponedUpdates.adGroups = [];
    }


    function reloadAccount (id) {
        return zemNavigationLegacyEndpoint.getAccount(id).then(function (accountData) {
            var accountCached = findAccountInNavTree(id);
            if (accounts.length === 0) {
                postponeDataUpdate(accountData);
                return accountData;
            }
            updateModel(accountCached.account, accountData.account);
            notifyCacheUpdate();
            return accountData;
        });
    }

    function reloadCampaign (id) {
        return zemNavigationLegacyEndpoint.getCampaign(id).then(function (campaignData) {
            if (accounts.length === 0) {
                postponeDataUpdate(campaignData);
                return campaignData;
            }
            var campaignCached = findCampaignInNavTree(id);
            updateModel(campaignCached.account, campaignData.account);
            updateModel(campaignCached.campaign, campaignData.campaign);
            notifyCacheUpdate();
            return campaignCached;
        });
    }

    function reloadAdGroup (id) {
        notifyAdGroupReloading(id, true);

        return zemNavigationLegacyEndpoint.getAdGroup(id).then(function (adGroupData) {
            if (accounts.length === 0) {
                postponeDataUpdate(adGroupData);
                return adGroupData;
            }
            var adGroupCached = findAdGroupInNavTree(id);
            updateModel(adGroupCached.account, adGroupData.account);
            updateModel(adGroupCached.campaign, adGroupData.campaign);
            updateModel(adGroupCached.adGroup, adGroupData.adGroup);
            notifyAdGroupReloading(id, false);

            notifyCacheUpdate();
            return adGroupCached;
        });
    }

    return {
        getAccount: getAccount,
        getCampaign: getCampaign,
        getAdGroup: getAdGroup,

        getAccountsAccess: getAccountsAccess,

        getUsesBCMv2: zemNavigationLegacyEndpoint.getUsesBCMv2,

        reload: reload,
        reloadAccount: reloadAccount,
        reloadCampaign: reloadCampaign,
        reloadAdGroup: reloadAdGroup,

        notifyAdGroupReloading: notifyAdGroupReloading,

        updateAllAccountsCache: updateAllAccountsCache,
        updateAdGroupCache: updateAdGroupCache,
        updateCampaignCache: updateCampaignCache,
        updateAccountCache: updateAccountCache,

        addAdGroupToCache: addAdGroupToCache,
        addCampaignToCache: addCampaignToCache,
        addAccountToCache: addAccountToCache,

        onUpdate: function (scope, callback) {
            var handler = $rootScope.$on('navigation-updated', callback);
            scope.$on('$destroy', handler);
        },

        onLoading: function (scope, callback) {
            var handler = $rootScope.$on('navigation-loading', callback);
            scope.$on('$destroy', handler);
        },

        onAdGroupLoading: function (scope, id, callback) {
            var handler = $rootScope.$on('navigation-adgroup-loading-' + id, callback);
            scope.$on('$destroy', handler);
        },

        getAccounts: function () {
            return accounts;
        },
    };
});

