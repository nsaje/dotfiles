angular.module('one.widgets').service('zemNavigationUtils', [function () {
    this.convertToEntityList = convertToEntityList;
    this.filterEntityList = filterEntityList;

    function convertToEntityList (entity) {
        var list = flattenNavigationHierarchy(entity);
        if (entity.type) {
            // If not hierarchy root (has type; account, campaign, ad group)
            // put entity at the beginning of the list
            list.unshift(entity);
        }
        return list;
    }

    function flattenNavigationHierarchy (entity, list) {
        if (!list) list = [];
        if (entity.children) {
            entity.children.forEach(function (child) {
                list.push(child);
                flattenNavigationHierarchy(child, list);
            });
        }
        return list;
    }

    function filterEntityList (list, query, filterArchived, filterAgency) {
        // Filter list using query and filter state (archived, etc.)
        // Keep parents in list (e.g. keep account and campaign if ad group is present in filtered list)

        query = query.toLowerCase();
        var filteredList = list;

        filteredList = filteredList.filter(function (item) {
            return !item.data.archived || filterArchived;
        });

        filteredList = filteredList.filter(function (item) {
            if (item.type !== constants.entityType.AD_GROUP) return true;
            return item.name.toLowerCase().indexOf(query) >= 0;
        });

        filteredList = filteredList.filter(function (item, idx) {
            if (item.type !== constants.entityType.CAMPAIGN) return true;
            if (filteredList[idx + 1] && filteredList[idx + 1].type === constants.entityType.AD_GROUP) return true;
            return item.name.toLowerCase().indexOf(query) >= 0;
        });

        filteredList = filteredList.filter(function (item, idx) {
            if (item.type !== constants.entityType.ACCOUNT) return true;
            if (filteredList[idx + 1] && filteredList[idx + 1].type === constants.entityType.CAMPAIGN) return true;
            if (filterAgency && item.data.agency && item.data.agency.toLowerCase().indexOf(query) >= 0) return true;
            return item.name.toLowerCase().indexOf(query) >= 0;
        });

        return filteredList;
    }

}]);
