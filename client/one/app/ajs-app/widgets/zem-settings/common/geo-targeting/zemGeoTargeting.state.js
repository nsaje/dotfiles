angular
    .module('one.widgets')
    .service('zemGeoTargetingStateService', function(
        zemGeoTargetingEndpoint,
        $q
    ) {
        this.createInstance = createInstance;

        var TOOLTIP_NOT_SUPPORTED_BY_OUTBRAIN = 'Not supported by Outbrain';
        var TOOLTIP_NOT_SUPPORTED_BY_YAHOO = 'Not supported by Yahoo!';

        var WARNING_DIFFERENT_LOCATION_LEVELS =
            'You are using different geographical features (city, country, ...). Note that if for example both the country United States and the city of New York are included, the whole US will be targeted.'; // eslint-disable-line max-len

        var FIELD_COUNTRY = 'countries';
        var FIELD_CITY = 'cities';
        var FIELD_REGION = 'regions';
        var FIELD_DMA = 'dma';
        var FIELD_ZIP = 'postalCodes';
        var GEO_TYPE_FIELDS = [
            FIELD_COUNTRY,
            FIELD_CITY,
            FIELD_REGION,
            FIELD_DMA,
        ];

        var TARGETING_SECTIONS_TEMPLATE = {};
        TARGETING_SECTIONS_TEMPLATE[constants.geolocationType.COUNTRY] = [];
        TARGETING_SECTIONS_TEMPLATE[constants.geolocationType.REGION] = [];
        TARGETING_SECTIONS_TEMPLATE[constants.geolocationType.DMA] = [];
        TARGETING_SECTIONS_TEMPLATE[constants.geolocationType.CITY] = [];

        var GEO_TYPE_TO_FIELD = {};
        GEO_TYPE_TO_FIELD[constants.geolocationType.COUNTRY] = FIELD_COUNTRY;
        GEO_TYPE_TO_FIELD[constants.geolocationType.REGION] = FIELD_REGION;
        GEO_TYPE_TO_FIELD[constants.geolocationType.DMA] = FIELD_DMA;
        GEO_TYPE_TO_FIELD[constants.geolocationType.CITY] = FIELD_CITY;
        GEO_TYPE_TO_FIELD[constants.geolocationType.ZIP] = FIELD_ZIP;

        function createInstance(propagateUpdate) {
            return new zemGeoTargetingStateService(propagateUpdate);
        }

        function zemGeoTargetingStateService(propagateUpdate) {
            this.getState = getState;
            this.updateTargeting = updateTargeting;
            this.refresh = refresh;
            this.addIncluded = addIncluded;
            this.addExcluded = addExcluded;
            this.removeLocation = removeLocation;

            var state = {
                locations: {
                    included: [],
                    excluded: [],
                    notSelected: [],
                },
                messages: {
                    warnings: [],
                },
            };

            var includedLocations;
            var excludedLocations;

            var geolocationMappingsCache = {};
            var searchResults = [];

            function getState() {
                return state;
            }

            function updateTargeting(included, excluded) {
                includedLocations = included;
                excludedLocations = excluded;

                fetchMappingsForUnmappedKeys(
                    includedLocations,
                    excludedLocations
                ).then(function(fetchedMappings) {
                    addMappingsToMappingsCache(fetchedMappings);
                    state.locations = generateTargetedLocations(
                        includedLocations,
                        excludedLocations
                    );
                    updateMessages(includedLocations);
                });
            }

            function fetchMappingsForUnmappedKeys(
                includedLocations,
                excludedLocations
            ) {
                var deferred = $q.defer();
                var unmappedKeys = getUnmappedKeys(
                    includedLocations,
                    excludedLocations
                );

                if (unmappedKeys.length > 0) {
                    zemGeoTargetingEndpoint
                        .map(unmappedKeys)
                        .then(function(mappings) {
                            deferred.resolve(mappings);
                        });
                } else {
                    deferred.resolve([]);
                }

                return deferred.promise;
            }

            function addMappingsToMappingsCache(fetchedMappings) {
                fetchedMappings.forEach(function(geolocation) {
                    geolocationMappingsCache[geolocation.key] = geolocation;
                });
            }

            function generateTargetedLocations(
                includedLocations,
                excludedLocations
            ) {
                var geolocation;
                var alreadySelectedIds = [];
                var included = angular.copy(TARGETING_SECTIONS_TEMPLATE);
                var excluded = angular.copy(TARGETING_SECTIONS_TEMPLATE);
                var notSelected = angular.copy(TARGETING_SECTIONS_TEMPLATE);

                GEO_TYPE_FIELDS.forEach(function(geoTypeField) {
                    if (includedLocations) {
                        includedLocations[geoTypeField].forEach(function(key) {
                            geolocation = geolocationMappingsCache[key];
                            if (geolocation) {
                                included[geolocation.type].push(
                                    generateLocationObject(geolocation)
                                );
                                alreadySelectedIds.push(key);
                            }
                        });
                    }
                    if (excludedLocations) {
                        excludedLocations[geoTypeField].forEach(function(key) {
                            geolocation = geolocationMappingsCache[key];
                            if (geolocation) {
                                excluded[geolocation.type].push(
                                    generateLocationObject(geolocation)
                                );
                                alreadySelectedIds.push(key);
                            }
                        });
                    }
                });

                var SECTION_RESULTS_SIZE = 10;
                var sectionItems = {};
                searchResults.forEach(function(geolocation) {
                    if (alreadySelectedIds.indexOf(geolocation.key) !== -1) {
                        return;
                    }
                    sectionItems[geolocation.type] =
                        sectionItems[geolocation.type] || 0;
                    if (sectionItems[geolocation.type] < SECTION_RESULTS_SIZE) {
                        sectionItems[geolocation.type]++;
                        notSelected[geolocation.type].push(
                            generateLocationObject(geolocation)
                        );
                    }
                });

                function flattenSections(sections) {
                    return []
                        .concat(sections[constants.geolocationType.COUNTRY])
                        .concat(sections[constants.geolocationType.REGION])
                        .concat(sections[constants.geolocationType.DMA])
                        .concat(sections[constants.geolocationType.CITY]);
                }

                var locations = {};
                locations.included = flattenSections(included);
                locations.excluded = flattenSections(excluded);
                locations.notSelected = flattenSections(notSelected);

                return locations;
            }

            var lastSearchTerm;
            function refresh(searchTerm) {
                if (searchTerm.length < 2) {
                    lastSearchTerm = null;
                    searchResults = [];
                    state.locations = generateTargetedLocations(
                        includedLocations,
                        excludedLocations
                    );
                    return;
                }
                lastSearchTerm = searchTerm;
                zemGeoTargetingEndpoint
                    .search(searchTerm)
                    .then(function(response) {
                        if (searchTerm !== lastSearchTerm) {
                            // There is a more recent search in progress
                            return;
                        }
                        searchResults = response;
                        state.locations = generateTargetedLocations(
                            includedLocations,
                            excludedLocations
                        );
                        lastSearchTerm = null;
                    });
            }

            function addIncluded(location) {
                geolocationMappingsCache[location.id] = location.geolocation;

                var fieldName = GEO_TYPE_TO_FIELD[location.geolocation.type];
                var updatedIncludedLocations = angular.copy(includedLocations);
                updatedIncludedLocations[fieldName].push(location.id);
                propagateUpdate({
                    includedLocations: updatedIncludedLocations,
                });
            }

            function addExcluded(location) {
                geolocationMappingsCache[location.id] = location.geolocation;

                var fieldName = GEO_TYPE_TO_FIELD[location.geolocation.type];
                var updatedExcludedLocations = angular.copy(excludedLocations);
                updatedExcludedLocations[fieldName].push(location.id);
                propagateUpdate({
                    excludedLocations: updatedExcludedLocations,
                });
            }

            function removeLocation(location) {
                var updatedIncludedLocations;
                var updatedExcludedLocations;

                var fieldName = GEO_TYPE_TO_FIELD[location.geolocation.type];

                var index = includedLocations[fieldName].indexOf(location.id);
                if (index !== -1) {
                    updatedIncludedLocations = angular.copy(includedLocations);
                    updatedIncludedLocations[fieldName].splice(index, 1);
                }

                index = excludedLocations[fieldName].indexOf(location.id);
                if (index !== -1) {
                    updatedExcludedLocations = angular.copy(excludedLocations);
                    updatedExcludedLocations[fieldName].splice(index, 1);
                }

                if (updatedIncludedLocations || updatedExcludedLocations) {
                    propagateUpdate({
                        includedLocations: updatedIncludedLocations,
                        excludedLocations: updatedExcludedLocations,
                    });
                }
            }

            function generateLocationObject(geolocation) {
                return {
                    id: geolocation.key,
                    section: constants.geolocationTypeText[geolocation.type],
                    name: geolocation.name,
                    title: geolocation.name,
                    badges: getLocationBadges(geolocation),
                    geolocation: geolocation,
                };
            }

            function getLocationBadges(geolocation) {
                var badges = [];
                if (!geolocation.outbrainId) {
                    badges.push({
                        class: 'outbrain',
                        text: TOOLTIP_NOT_SUPPORTED_BY_OUTBRAIN,
                    });
                }
                if (!geolocation.woeid) {
                    badges.push({
                        class: 'yahoo',
                        text: TOOLTIP_NOT_SUPPORTED_BY_YAHOO,
                    });
                }
                return badges;
            }

            function getUnmappedKeys(includedLocations, excludedLocations) {
                return getLocationKeysWithoutZips(includedLocations)
                    .concat(getLocationKeysWithoutZips(excludedLocations))
                    .filter(function(key) {
                        return !geolocationMappingsCache[key];
                    });
            }

            // prettier-ignore
            function updateMessages(includedLocations) { // eslint-disable-line complexity
                var warnings = [];
                var includedLocationsWithoutZips = getLocationKeysWithoutZips(
                    includedLocations
                );

                var i,
                    geolocation,
                    hasCountry = false,
                    hasOther = false;
                for (i = 0; i < includedLocationsWithoutZips.length; i++) {
                    geolocation = geolocationMappingsCache[includedLocationsWithoutZips[i]];
                    if (
                        geolocation &&
                        geolocation.type === constants.geolocationType.COUNTRY
                    ) {
                        hasCountry = true;
                    } else {
                        hasOther = true;
                    }
                }
                if (hasCountry && hasOther) {
                    warnings.push(WARNING_DIFFERENT_LOCATION_LEVELS);
                }

                state.messages.warnings = warnings;
            }

            function getLocationKeysWithoutZips(locations) {
                var keys = [];
                [FIELD_COUNTRY, FIELD_REGION, FIELD_CITY, FIELD_DMA].forEach(
                    function(geoTypeField) {
                        locations[geoTypeField].forEach(function(key) {
                            keys.push(key);
                        });
                    }
                );
                return keys;
            }
        }
    });
