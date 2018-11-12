angular.module('one.widgets').service('zemNavigationUtils', function() {
    this.convertToEntityList = convertToEntityList;
    this.filterEntityList = filterEntityList;

    var ACCOUNTS_EXCLUDED_FROM_SEARCH = [constants.specialAccount.OEN];

    function convertToEntityList(entity) {
        var list = flattenNavigationHierarchy(entity);
        if (entity.type) {
            // If not hierarchy root (has type; account, campaign, ad group)
            // put entity at the beginning of the list
            list.unshift(entity);
        }
        return list;
    }

    function flattenNavigationHierarchy(entity, list) {
        if (!list) list = [];
        if (entity.children) {
            entity.children.forEach(function(child) {
                list.push(child);
                flattenNavigationHierarchy(child, list);
            });
        }
        return list;
    }

    function filterEntityList(list, query, filterArchived, filterAgency) {
        // Filter list using query and filter state (archived, etc.)
        // Keep parents in list (e.g. keep account and campaign if ad group is present in filtered list)

        query = query.toLowerCase();
        var idQuery = parseInt(query, 10);
        var filteredList = list;

        filteredList = filteredList.filter(function(item) {
            var isAccountExcluded = isAccountExcludedFromSearch(item);
            var isItemIncluded = !item.data.archived || filterArchived;
            return !isAccountExcluded && isItemIncluded;
        });

        filteredList = filteredList.filter(function(item) {
            if (item.type !== constants.entityType.AD_GROUP) return true;
            if (filterAgency && isFilteredByAgency(item, query)) return true;
            return (
                (idQuery && isFilteredById(item, idQuery)) ||
                isFilteredByName(item, query)
            );
        });

        filteredList = filteredList.filter(function(item, idx) {
            if (item.type !== constants.entityType.CAMPAIGN) return true;
            if (
                filteredList[idx + 1] &&
                filteredList[idx + 1].type === constants.entityType.AD_GROUP
            )
                return true;
            if (filterAgency && isFilteredByAgency(item, query)) return true;
            return (
                (idQuery && isFilteredById(item, idQuery)) ||
                isFilteredByName(item, query)
            );
        });

        filteredList = filteredList.filter(function(item, idx) {
            if (item.type !== constants.entityType.ACCOUNT) return true;
            if (
                filteredList[idx + 1] &&
                filteredList[idx + 1].type === constants.entityType.CAMPAIGN
            )
                return true;
            if (filterAgency && isFilteredByAgency(item, query)) return true;
            return (
                (idQuery && isFilteredById(item, idQuery)) ||
                isFilteredByName(item, query)
            );
        });

        return filteredList;
    }

    function isAccountExcludedFromSearch(item) {
        var account = getAccountFromItem(item);
        return ACCOUNTS_EXCLUDED_FROM_SEARCH.indexOf(account.id) !== -1;
    }

    function isFilteredByAgency(item, query) {
        var account = getAccountFromItem(item);
        return (
            account.data.agency &&
            account.data.agency.toLowerCase().indexOf(query) >= 0
        );
    }

    function getAccountFromItem(item) {
        switch (item.type) {
            case constants.entityType.AD_GROUP:
                return item.parent.parent;
            case constants.entityType.CAMPAIGN:
                return item.parent;
            default:
                return item;
        }
    }

    function isFilteredById(item, idQuery) {
        return parseInt(item.id) === idQuery;
    }

    function isFilteredByName(item, query) {
        return item.name.toLowerCase().indexOf(query) >= 0;
    }
});
