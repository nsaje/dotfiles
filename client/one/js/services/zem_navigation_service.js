"use strict";

oneApp.factory('zemNavigationService', ['$q', '$location', 'api', function($q, $location, api) {

    var accounts = [], loading = false, lastSyncTS = null;

    function _findAccountInNavTree(id) {
        var strId = id.toString();

        for(var i = 0; i < accounts.length; i++) {
            if (accounts[i].id.toString() === strId) {
                return {
                    account: accounts[i]
                };
            }
        }
        return undefined;
    };

    function _findCampaignInNavTree(id) {
        var strId = id.toString();
        for(var i = 0; i < accounts.length; i++) {
            for(var j = 0; j < accounts[i].campaigns.length; j++) {
                if (accounts[i].campaigns[j].id.toString() === strId) {
                    return {
                        account: accounts[i],
                        campaign: accounts[i].campaigns[j]
                    };
                }
            }
        }
        return undefined;
    }

    function _findAdGroupInNavTree(id) {
        var strId = id.toString();
        for(var i = 0; i < accounts.length; i++) {
            for(var j = 0; j < accounts[i].campaigns.length; j++) {
                for(var k = 0; k < accounts[i].campaigns[j].adGroups.length; k++) {
                    if (accounts[i].campaigns[j].adGroups[k].id.toString() === strId) {
                        return {
                            account: accounts[i],
                            campaign: accounts[i].campaigns[j],
                            adGroup: accounts[i].campaigns[j].adGroups[k]
                        };
                    }
                }
            }
        }
        return undefined;
    }

    function _findHasAccountsInNavTree() {
        return !!accounts;
    };

    function _loadData(id, apiFunc, searchCacheFunc) {
        // Loads data from cache or calls api if data is not in cache

        if (accounts.length === 0) {
            return apiFunc(id).then(function(data) {

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
    };

    function getAccount(id) {
        return _loadData(
            id,
            api.navigation.getAccount,
            _findAccountInNavTree
        );
    };

    function getCampaign(id) {
        return _loadData(
            id,
            api.navigation.getCampaign,
            _findCampaignInNavTree
        );
    };

    function getAdGroup(id) {
        return _loadData(
            id,
            api.navigation.getAdGroup,
            _findAdGroupInNavTree
        );
    };

    function getAccountsAccess() {
        return _loadData(
            null,
            api.navigation.getAccountsAccess,
            _findHasAccountsInNavTree
        );
    };

    function _updateModel(model, dataObjOrFunc) {
        // updates a model with provided function or replaces key-values pairs in it
        // if object is provided
        if (typeof dataObjOrFunc === "function") {
            dataObjOrFunc(model);
        } else {
            Object.keys(dataObjOrFunc).forEach(function(key) {
                model[key] = dataObjOrFunc[key];
            });
        }
    }

    function _notifyCacheUpdate() {
        lastSyncTS = Date();
    }

    function updateAllAccountsCache(dataObjOrFunc) {
        if (typeof dataObjOrFunc === "function") {
            dataObjOrFunc(accounts);
        } else {
            Object.keys(dataObjOrFunc).forEach(function(key) {
                accounts[key] = dataObjOrFunc[key];
            });
        }
        _notifyCacheUpdate();
    }

    function updateAccountCache(id, dataObjOrFunc) {
        var fromCache = _findAccountInNavTree(id);
        _updateModel(fromCache.account, dataObjOrFunc);
        _notifyCacheUpdate();
    }

    function updateCampaignCache(id, dataObjOrFunc) {
        var fromCache = _findCampaignInNavTree(id);
        _updateModel(fromCache.campaign, dataObjOrFunc);
        _notifyCacheUpdate();
    }

    function updateAdGroupCache(id, dataObjOrFunc) {
        var fromCache = _findAdGroupInNavTree(id);
        _updateModel(fromCache.adGroup, dataObjOrFunc);
        _notifyCacheUpdate();
    }

    function reload() {
        loading = true;
        return api.navigation.list().then(function(data) {
            accounts = data;

            _notifyCacheUpdate();

            loading = false;
            return data;
        });
    };

    function reloadAccount(id) {
        return api.navigation.getAccount(id).then(function(accountData) {
            var accountCached = _findAccountInNavTree(id);
            _updateModel(accountCached.account, accountData.account);
            _notifyCacheUpdate();
            return accountData;
        });
    };

    function reloadCampaign(id) {
        return api.navigation.getCampaign(id).then(function(campaignData) {
            var campaignCached = _findCampaignInNavTree(id);
            _updateModel(campaignCached.account, campaignData.account);
            _updateModel(campaignCached.campaign, campaignData.campaign);
            _notifyCacheUpdate();
            return campaignCached;
        });
    };

    function reloadAdGroup(id) {
        return api.navigation.getAdGroup(id).then(function(adGroupData) {

            var adGroupCached = _findAdGroupInNavTree(id);
            _updateModel(adGroupCached.account, adGroupData.account);
            _updateModel(adGroupCached.campaign, adGroupData.campaign);
            _updateModel(adGroupCached.adGroup, adGroupData.adGroup);
            _notifyCacheUpdate();
            return adGroupCached;
        });
    };

    return {
        getAccount: getAccount,
        getCampaign: getCampaign,
        getAdGroup: getAdGroup,

        getAccountsAccess: getAccountsAccess,

        reload: reload,
        reloadAccount: reloadAccount,
        reloadCampaign: reloadCampaign,
        reloadAdGroup: reloadAdGroup,

        updateAllAccountsCache: updateAllAccountsCache,
        updateAdGroupCache: updateAdGroupCache,
        updateCampaignCache: updateCampaignCache,
        updateAccountCache: updateAccountCache,

        isLoadInProgress: function() {
            return loading;
        },

        getAccounts: function() {
            return accounts;
        },

        // used for demo only
        setAccounts: function(accs) {
            accounts = accs;
        },

        lastSyncTS: function() {
            return lastSyncTS;
        }
    };
}]);

