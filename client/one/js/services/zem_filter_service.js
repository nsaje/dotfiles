/* globals JSON */
"use strict";

oneApp.factory('zemFilterService', ['$location', function ($location) {
    // Because filteredSources is being watched (through getFilteredSources function) from
    // different controllers, it has to always point to the same array. Special care is taken
    // to never replace the reference (no assignments to this variable) so the array is
    // always modified in place.
    var filteredSources = [];
    var filteredAgencies = [];
    var filteredAccountTypes = [];
    var showArchived = false;
    var showBlacklistedPublisher = false;
    var blacklistedPublisherFilter = null;

    function init (user) {
        var filteredSourcesLocation = $location.search().filtered_sources;
        if (filteredSourcesLocation) {
            Array.prototype.splice.apply(filteredSources, [0, filteredSources.length].concat(filteredSourcesLocation.split(',')));
        }

        var filteredAgenciesLocation = $location.search().filtered_agencies;
        if (filteredAgenciesLocation) {
            Array.prototype.splice.apply(filteredAgencies, [0, filteredAgencies.length].concat(filteredAgenciesLocation.split(',')));
        }

        var filteredAccountTypesLocation = $location.search().filtered_account_types;
        if (filteredAccountTypesLocation) {
            Array.prototype.splice.apply(filteredAccountTypes, [0, filteredAccountTypes.length].concat(filteredAccountTypesLocation.split(',')));
        }

        showArchived = $location.search().show_archived || false;

        if ('zemauth.can_see_publishers' in user.permissions) {
            blacklistedPublisherFilter = $location.search().show_blacklisted_publishers || null;
        }
    }

    function setFilteredAccountTypeLocation () {
        if (filteredAgencies.length > 0) {
            $location.search('filtered_account_types', filteredAccountTypes.join(','));
        } else {
            $location.search('filtered_account_types', null);
        }
    }

    function setFilteredAgenciesLocation () {
        if (filteredAgencies.length > 0) {
            $location.search('filtered_agencies', filteredAgencies.join(','));
        } else {
            $location.search('filtered_agencies', null);
        }
    }

    function setFilteredSourcesLocation () {
        if (filteredSources.length > 0) {
            $location.search('filtered_sources', filteredSources.join(','));
        } else {
            $location.search('filtered_sources', null);
        }
    }

    function setShowArchivedLocation () {
        if (showArchived) {
            $location.search('show_archived', showArchived);
        } else {
            $location.search('show_archived', null);
        }
    }

    function setBlacklistedPublishersLocation () {
        if (blacklistedPublisherFilter) {
            $location.search('show_blacklisted_publishers', blacklistedPublisherFilter);
        } else {
            $location.search('show_blacklisted_publishers', null);
        }
    }

    function getFilteredSources () {
        return filteredSources;
    }

    function getFilteredAgencies () {
        return filteredAgencies;
    }

    function getFilteredAccountTypes () {
        return filteredAccountTypes;
    }

    function isSourceFiltered (sourceId) {
        for (var i = 0; i < filteredSources.length; i++) {
            if (filteredSources[i] === sourceId) {
                return true;
            }
        }

        return false;
    }

    function isArchivedFilterOn () {
        return showArchived;
    }

    function isPublisherBlacklistFilterOn () {
        return blacklistedPublisherFilter !== null && blacklistedPublisherFilter !== 'all';
    }

    function isSourceFilterOn () {
        return filteredSources.length > 0;
    }

    function isAgencyFiltered (agencyId) {
        for (var i = 0; i < filteredAgencies.length; i++) {
            if (filteredAgencies[i] === agencyId) {
                return true;
            }
        }
        return false;
    }

    function isAgencyFilterOn () {
        return filteredAgencies.length > 0;
    }

    function addFilteredAgency (agencyId) {
        if (filteredAgencies.indexOf(agencyId) === -1) {
            filteredAgencies.push(agencyId);
            filteredAgencies.sort(function (a, b) { return parseInt(a) - parseInt(b); });
        }

        setFilteredAgenciesLocation();
    }

    function removeFilteredAgency (agencyId) {
        var ix = filteredAgencies.indexOf(agencyId);
        if (ix > -1) {
            filteredAgencies.splice(ix, 1);
        }

        setFilteredAgenciesLocation();
    }

    function isAccountTypeFiltered (accountTypeId) {
        for (var i = 0; i < filteredAccountTypes.length; i++) {
            if (filteredAccountTypes[i] === accountTypeId) {
                return true;
            }
        }
        return false;
    }

    function isAccountTypeFilterOn () {
        return filteredAccountTypes.length > 0;
    }

    function addFilteredAccountType (accountTypeId) {
        if (filteredAccountTypes.indexOf(accountTypeId) === -1) {
            filteredAccountTypes.push(accountTypeId);
            filteredAccountTypes.sort(function (a, b) { return parseInt(a) - parseInt(b); });
        }

        setFilteredAccountTypesLocation();
    }

    function removeFilteredAccountType (accountTypeId) {
        var ix = filteredAccountTypes.indexOf(accountTypeId);
        if (ix > -1) {
            filteredAccountTypes.splice(ix, 1);
        }

        setFilteredAccountTypesLocation();
    }

    function addFilteredSource (sourceId) {
        if (filteredSources.indexOf(sourceId) === -1) {
            filteredSources.push(sourceId);
            filteredSources.sort(function (a, b) { return parseInt(a) - parseInt(b); });
        }

        setFilteredSourcesLocation();
    }

    function removeFilteredSource (sourceId) {
        var ix = filteredSources.indexOf(sourceId);
        if (ix > -1) {
            filteredSources.splice(ix, 1);
        }

        setFilteredSourcesLocation();
    }

    function exclusivelyFilterSource (sourceId) {
        filteredSources.splice(0, filteredSources.length, sourceId);
        setFilteredSourcesLocation();
    }

    function removeFiltering () {
        filteredSources.splice(0, filteredSources.length);
        filteredAgencies.splice(0, filteredAgencies.length);

        setFilteredSourcesLocation();
        setFilteredAgenciesLocation();
        setFilteredAccountTypes();
        setShowArchivedLocation();

        blacklistedPublisherFilter = null;
        setBlacklistedPublishers(null);
    }

    function getShowArchived () {
        return showArchived;
    }

    function setShowArchived (newValue) {
        showArchived = newValue;
        setShowArchivedLocation();
    }

    function getBlacklistedPublishers () {
        return blacklistedPublisherFilter;
    }

    function setBlacklistedPublishers (newValue) {
        blacklistedPublisherFilter = newValue;
        setBlacklistedPublishersLocation();
    }

    function getShowBlacklistedPublishers () {
        return showBlacklistedPublisher;
    }

    function setShowBlacklistedPublishers (newValue) {
        showBlacklistedPublisher = newValue;
    }

    return {
        init: init,
        isArchivedFilterOn: isArchivedFilterOn,
        getShowArchived: getShowArchived,
        setShowArchived: setShowArchived,
        getFilteredSources: getFilteredSources,
        getFilteredAgencies: getFilteredAgencies,
        isSourceFiltered: isSourceFiltered,
        isSourceFilterOn: isSourceFilterOn,
        isAgencyFiltered: isAgencyFiltered,
        isAgencyFilterOn: isAgencyFilterOn,
        addFilteredAgency: addFilteredAgency,
        removeFilteredAgency: removeFilteredAgency,
        isAccountTypeFiltered: isAccountTypeFiltered,
        isAccountTypeFilterOn: isAccountTypeFilterOn,
        addFilteredAccountType: addFilteredAccountType,
        removeFilteredAccountType: removeFilteredAccountType,
        addFilteredSource: addFilteredSource,
        exclusivelyFilterSource: exclusivelyFilterSource,
        removeFilteredSource: removeFilteredSource,
        removeFiltering: removeFiltering,
        isPublisherBlacklistFilterOn: isPublisherBlacklistFilterOn,
        getBlacklistedPublishers: getBlacklistedPublishers,
        setBlacklistedPublishers: setBlacklistedPublishers,
        getShowBlacklistedPublishers: getShowBlacklistedPublishers,
        setShowBlacklistedPublishers: setShowBlacklistedPublishers
    };
}]);


