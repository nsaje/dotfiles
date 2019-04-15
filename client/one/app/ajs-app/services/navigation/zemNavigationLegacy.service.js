angular
    .module('one.services')
    .factory('zemNavigationService', function(
        $rootScope,
        $q,
        zemNavigationLegacyEndpoint,
        zemEntitiesUpdatesService
    ) {
        // eslint-disable-line max-len

        var postoponedUpdates = {
            accounts: [],
            campaigns: [],
            adGroups: [],
        };

        var accounts = [];
        var accountsLoaded = false;
        var accountsAccess;

        function findAccountInNavTree(id) {
            if (!accountsLoaded) return;

            var strId = id.toString();

            for (var i = 0; i < accounts.length; i++) {
                if (accounts[i].id.toString() === strId) {
                    return {
                        account: accounts[i],
                    };
                }
            }
        }

        function findCampaignInNavTree(id) {
            if (!accountsLoaded) return;

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
        }

        function findAdGroupInNavTree(id) {
            if (!accountsLoaded) return;

            var strId = id.toString();
            for (var i = 0; i < accounts.length; i++) {
                for (var j = 0; j < accounts[i].campaigns.length; j++) {
                    for (
                        var k = 0;
                        k < accounts[i].campaigns[j].adGroups.length;
                        k++
                    ) {
                        if (
                            accounts[i].campaigns[j].adGroups[
                                k
                            ].id.toString() === strId
                        ) {
                            return {
                                account: accounts[i],
                                campaign: accounts[i].campaigns[j],
                                adGroup: accounts[i].campaigns[j].adGroups[k],
                            };
                        }
                    }
                }
            }
        }

        function loadData(id, apiFunc, searchCacheFunc) {
            // Loads data from cache or calls api if data is not in cache

            var data = searchCacheFunc(id);
            if (data) {
                // simulate api call - return a promise, but resolve it
                // beforehand just to preserve the api behaviour
                return $q.resolve(data);
            }

            return apiFunc(id).then(function(data) {
                return data;
            });
        }

        function getAccount(id) {
            return loadData(
                id,
                zemNavigationLegacyEndpoint.getAccount,
                findAccountInNavTree
            );
        }

        function getCampaign(id) {
            return loadData(
                id,
                zemNavigationLegacyEndpoint.getCampaign,
                findCampaignInNavTree
            );
        }

        function getAdGroup(id) {
            return loadData(
                id,
                zemNavigationLegacyEndpoint.getAdGroup,
                findAdGroupInNavTree
            );
        }

        function getAccountsAccess() {
            var deferred = $q.defer();

            if (accountsAccess) {
                deferred.resolve(accountsAccess);
            } else {
                zemNavigationLegacyEndpoint
                    .getAccountsAccess()
                    .then(function(data) {
                        accountsAccess = data;
                        deferred.resolve(accountsAccess);
                    });
            }

            return deferred.promise;
        }

        function updateModel(model, dataObjOrFunc) {
            // updates a model with provided function or replaces key-values pairs in it
            // if object is provided
            if (!model) return;
            if (typeof dataObjOrFunc === 'function') {
                dataObjOrFunc(model);
            } else {
                Object.keys(dataObjOrFunc).forEach(function(key) {
                    model[key] = dataObjOrFunc[key];
                });
            }
        }

        function notifyCacheUpdate() {
            $rootScope.$emit('navigation-updated');
        }

        function notifyAdGroupReloading(id, reloading) {
            $rootScope.$emit('navigation-adgroup-loading-' + id);
            var adGroupCached = findAdGroupInNavTree(id);
            if (adGroupCached) {
                updateModel(adGroupCached.adGroup, {
                    reloading: reloading,
                });
            }
        }

        function init() {
            zemEntitiesUpdatesService
                .getAllUpdates$()
                .subscribe(reloadOnEntityUpdate);

            $rootScope.$emit('navigation-loading', true);
            return zemNavigationLegacyEndpoint
                .list(true)
                .then(function(data) {
                    for (var i = 0; i < data.length; i++) {
                        for (var j = 0; j < data[i].campaigns.length; j++) {
                            for (
                                var k = 0;
                                k < data[i].campaigns[j].adGroups.length;
                                k++
                            ) {
                                data[i].campaigns[j].adGroups[
                                    k
                                ].reloading = true;
                            }
                        }
                    }
                    accounts = data;
                    notifyCacheUpdate();
                    zemNavigationLegacyEndpoint.list().then(function(data) {
                        accounts = data;
                        accountsLoaded = true;
                        updatePostponedData();
                        notifyCacheUpdate();
                    });
                    return data;
                })
                .finally(function() {
                    $rootScope.$emit('navigation-loading', false);
                });
        }

        function reload() {
            $rootScope.$emit('navigation-loading', true);
            return zemNavigationLegacyEndpoint
                .list()
                .then(function(data) {
                    accounts = data;
                    accountsLoaded = true;
                    updatePostponedData();
                    notifyCacheUpdate();
                    return data;
                })
                .finally(function() {
                    $rootScope.$emit('navigation-loading', false);
                });
        }

        function postponeDataUpdate(data) {
            if (data.account) postoponedUpdates.accounts.push(data.account);
            if (data.campaign) postoponedUpdates.campaigns.push(data.campaign);
            if (data.adGroup) postoponedUpdates.adGroups.push(data.adGroup);
        }

        function updatePostponedData() {
            postoponedUpdates.accounts.forEach(function(account) {
                updateModel(findAccountInNavTree(account.id).account, account);
            });
            postoponedUpdates.campaigns.forEach(function(campaign) {
                updateModel(
                    findCampaignInNavTree(campaign.id).campaign,
                    campaign
                );
            });
            postoponedUpdates.adGroups.forEach(function(adGroup) {
                updateModel(findAdGroupInNavTree(adGroup.id).adGroup, adGroup);
            });

            postoponedUpdates.accounts = [];
            postoponedUpdates.campaigns = [];
            postoponedUpdates.adGroups = [];
        }

        function reloadOnEntityUpdate(entityUpdate) {
            if (entityUpdate.type === constants.entityType.ACCOUNT) {
                return reloadAccount(entityUpdate.id);
            }
            if (entityUpdate.type === constants.entityType.CAMPAIGN) {
                return reloadCampaign(entityUpdate.id);
            }
            if (entityUpdate.type === constants.entityType.AD_GROUP) {
                return reloadAdGroup(entityUpdate.id);
            }
        }

        function reloadAccount(id) {
            return zemNavigationLegacyEndpoint
                .getAccount(id)
                .then(function(data) {
                    var accountCached = findAccountInNavTree(id);
                    if (accountCached) {
                        updateModel(accountCached.account, data.account);
                    } else {
                        accountCached = addAccountToCache(data);
                    }
                    if (!accountsLoaded) {
                        postponeDataUpdate(data);
                    }
                    notifyCacheUpdate();
                    return accountCached;
                });
        }

        function reloadCampaign(id) {
            return zemNavigationLegacyEndpoint
                .getCampaign(id)
                .then(function(data) {
                    var campaignCached = findCampaignInNavTree(id);
                    if (campaignCached) {
                        updateModel(campaignCached.account, data.account);
                        updateModel(campaignCached.campaign, data.campaign);
                    } else {
                        campaignCached = addCampaignToCache(data);
                    }
                    if (!accountsLoaded) {
                        postponeDataUpdate(data);
                    }
                    notifyCacheUpdate();
                    return campaignCached;
                });
        }

        function reloadAdGroup(id) {
            notifyAdGroupReloading(id, true);

            return zemNavigationLegacyEndpoint
                .getAdGroup(id)
                .then(function(data) {
                    var adGroupCached = findAdGroupInNavTree(id);
                    if (adGroupCached) {
                        updateModel(adGroupCached.account, data.account);
                        updateModel(adGroupCached.campaign, data.campaign);
                        updateModel(adGroupCached.adGroup, data.adGroup);
                    } else {
                        adGroupCached = addAdGroupToCache(data);
                    }
                    if (!accountsLoaded) {
                        postponeDataUpdate(data);
                    }
                    notifyAdGroupReloading(id, false);
                    notifyCacheUpdate();
                    return adGroupCached;
                });
        }

        function addAccountToCache(data) {
            data.account.campaigns = [];
            accounts.push(data.account);
            return {
                account: data.account,
            };
        }

        function addCampaignToCache(data) {
            var accountCached = findAccountInNavTree(data.account.id);
            if (!accountCached) {
                accountCached = addAccountToCache(data);
            }
            data.campaign.adGroups = [];
            accountCached.account.campaigns.push(data.campaign);
            return {
                account: data.account,
                campaign: data.campaign,
            };
        }

        function addAdGroupToCache(data) {
            var campaignCached = findCampaignInNavTree(data.campaign.id);
            if (!campaignCached) {
                campaignCached = addCampaignToCache(data);
            }
            campaignCached.campaign.adGroups.push(data.adGroup);
            return {
                account: data.account,
                campaign: data.campaign,
                adGroup: data.adGroup,
            };
        }

        return {
            getAccount: getAccount,
            getCampaign: getCampaign,
            getAdGroup: getAdGroup,

            getAccountsAccess: getAccountsAccess,

            getUsesBCMv2: zemNavigationLegacyEndpoint.getUsesBCMv2,

            init: init,
            reload: reload,
            reloadAccount: reloadAccount,
            reloadCampaign: reloadCampaign,
            reloadAdGroup: reloadAdGroup,

            notifyAdGroupReloading: notifyAdGroupReloading,

            onUpdate: function(scope, callback) {
                var handler = $rootScope.$on('navigation-updated', callback);
                scope.$on('$destroy', handler);
            },

            onLoading: function(scope, callback) {
                var handler = $rootScope.$on('navigation-loading', callback);
                scope.$on('$destroy', handler);
            },

            onAdGroupLoading: function(scope, id, callback) {
                var handler = $rootScope.$on(
                    'navigation-adgroup-loading-' + id,
                    callback
                );
                scope.$on('$destroy', handler);
            },

            getAccounts: function() {
                return accounts;
            },

            isFullyLoaded: function() {
                return accountsLoaded;
            },
        };
    });
