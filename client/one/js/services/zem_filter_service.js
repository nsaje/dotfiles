/* globals JSON */
"use strict"

oneApp.factory('zemFilterService', ['$location', 'zemUserSettings', function($location, zemUserSettings) {
    var filtering = {
        filteredSources: [],
        showArchived: false,
        init: init
    };

    function init(user) {
        if ('zemauth.filter_sources' in user.permissions) {
            filtering.filteredSources = zemUserSettings.getValue('filteredSources', null, true) || [];
            if (typeof(filtering.filteredSources) !== 'undefined' && filtering.filteredSources.length > 0) {
                $location.search('filtered_sources', filtering.filteredSources.join(','));
            }
        }

        if ('zemauth.view_archived_entities' in user.permissions) {
            filtering.showArchived = zemUserSettings.getValue('showArchived', null, false) || false;
            if (filtering.showArchived) {
                $location.search('show_archived', filtering.showArchived);
            }
        }
    }

    return filtering;
}]);
