/* globals JSON */
"use strict"

oneApp.factory('zemFilterService', ['$location', 'zemUserSettings', function($location, zemUserSettings) {
    var filtering = {
        filteredSources: [],
        showArchived: false,
        init: init
    };

    function init() {
        filtering.filteredSources = zemUserSettings.getValue('filteredSources', null, true);
        filtering.showArchived = zemUserSettings.getValue('showArchived', null, false);

        if (filtering.filteredSources.length > 0) {
            $location.search('filtered_sources', filtering.filteredSources.join(','));
        }

        if (filtering.showArchived) {
            $location.search('show_archived', filtering.showArchived);
        }
    }

    return filtering;
}]);
