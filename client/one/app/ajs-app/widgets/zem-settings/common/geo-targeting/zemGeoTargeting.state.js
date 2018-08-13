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
        var INFO_OUTBRAIN_EXCLUDED =
            "Outbrain media source will be paused because it doesn't support excluded locations."; // eslint-disable-line max-len
        var INFO_OUTBRAIN_INCLUDED =
            "Outbrain media source will be paused because it doesn't support any of the included locations."; // eslint-disable-line max-len
        var INFO_YAHOO_EXCLUDED =
            "Yahoo media source will be paused because it doesn't support all the excluded locations."; // eslint-disable-line max-len
        var INFO_YAHOO_INCLUDED =
            "Yahoo media source will be paused because it doesn't support any of the included locations."; // eslint-disable-line max-len

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

        var TARGETING_REGIONS_TEMPLATE = {};
        TARGETING_REGIONS_TEMPLATE[FIELD_COUNTRY] = [];
        TARGETING_REGIONS_TEMPLATE[FIELD_REGION] = [];
        TARGETING_REGIONS_TEMPLATE[FIELD_DMA] = [];
        TARGETING_REGIONS_TEMPLATE[FIELD_CITY] = [];
        TARGETING_REGIONS_TEMPLATE[FIELD_ZIP] = [];

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

        function createInstance(entity) {
            return new zemGeoTargetingStateService(entity);
        }

        function zemGeoTargetingStateService(entity) {
            this.getState = getState;
            this.init = init;
            this.refresh = refresh;
            this.addIncluded = addIncluded;
            this.addExcluded = addExcluded;
            this.removeTargeting = removeTargeting;

            var state = {
                targetings: {
                    included: [],
                    excluded: [],
                    notSelected: [],
                },
                messages: {
                    warnings: [],
                    infos: [],
                },
            };

            var geolocationMappings = {};
            var searchResults = [];

            function getState() {
                return state;
            }

            function init() {
                if (!entity.settings.targetRegions) {
                    entity.settings.targetRegions = angular.copy(
                        TARGETING_REGIONS_TEMPLATE
                    );
                }
                if (!entity.settings.exclusionTargetRegions) {
                    entity.settings.exclusionTargetRegions = angular.copy(
                        TARGETING_REGIONS_TEMPLATE
                    );
                }

                fetchMappings().then(function(mappings) {
                    geolocationMappings = mappings;
                    state.targetings = getTargetings();
                    updateMessages();
                });
            }

            function getTargetings() {
                var geolocation;
                var alreadySelectedIds = [];
                var included = angular.copy(TARGETING_SECTIONS_TEMPLATE);
                var excluded = angular.copy(TARGETING_SECTIONS_TEMPLATE);
                var notSelected = angular.copy(TARGETING_SECTIONS_TEMPLATE);

                GEO_TYPE_FIELDS.forEach(function(geoTypeField) {
                    entity.settings.targetRegions[geoTypeField].forEach(
                        function(key) {
                            geolocation = geolocationMappings[key];
                            if (geolocation) {
                                included[geolocation.type].push(
                                    generateGeolocationObject(geolocation)
                                );
                                alreadySelectedIds.push(key);
                            }
                        }
                    );
                    entity.settings.exclusionTargetRegions[
                        geoTypeField
                    ].forEach(function(key) {
                        geolocation = geolocationMappings[key];
                        if (geolocation) {
                            excluded[geolocation.type].push(
                                generateGeolocationObject(geolocation)
                            );
                            alreadySelectedIds.push(key);
                        }
                    });
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
                            generateGeolocationObject(geolocation)
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

                var targetings = {};
                targetings.included = flattenSections(included);
                targetings.excluded = flattenSections(excluded);
                targetings.notSelected = flattenSections(notSelected);

                return targetings;
            }

            var lastSearchTerm;
            function refresh(searchTerm) {
                if (searchTerm.length < 2) {
                    lastSearchTerm = null;
                    searchResults = [];
                    state.targetings = getTargetings();
                    return;
                }
                lastSearchTerm = searchTerm;
                zemGeoTargetingEndpoint
                    .search(searchTerm)
                    .then(function(response) {
                        if (searchTerm !== lastSearchTerm) return; // There is a more recent search in progress

                        searchResults = response;
                        state.targetings = getTargetings();
                        lastSearchTerm = null;
                    });
            }

            function addIncluded(targeting) {
                if (!entity.settings.targetRegions) {
                    entity.settings.targetRegions = angular.copy(
                        TARGETING_REGIONS_TEMPLATE
                    );
                }
                var fieldName = GEO_TYPE_TO_FIELD[targeting.geolocation.type];
                var newRegions = angular.copy(entity.settings.targetRegions);
                newRegions[fieldName].push(targeting.id);
                entity.settings.targetRegions = newRegions;

                geolocationMappings[targeting.id] = targeting.geolocation;
                state.targetings = getTargetings();
                updateMessages();
            }

            function addExcluded(targeting) {
                if (!entity.settings.exclusionTargetRegions) {
                    entity.settings.exclusionTargetRegions = angular.copy(
                        TARGETING_REGIONS_TEMPLATE
                    );
                }
                var fieldName = GEO_TYPE_TO_FIELD[targeting.geolocation.type];
                var newRegions = angular.copy(
                    entity.settings.exclusionTargetRegions
                );
                newRegions[fieldName].push(targeting.id);
                entity.settings.exclusionTargetRegions = newRegions;

                geolocationMappings[targeting.id] = targeting.geolocation;
                state.targetings = getTargetings();
                updateMessages();
            }

            function removeTargeting(targeting) {
                var fieldName = GEO_TYPE_TO_FIELD[targeting.geolocation.type];
                var index = entity.settings.targetRegions[fieldName].indexOf(
                    targeting.id
                );
                var newRegions;
                if (index !== -1) {
                    newRegions = angular.copy(entity.settings.targetRegions);
                    newRegions[fieldName].splice(index, 1);
                    entity.settings.targetRegions = newRegions;
                }

                index = entity.settings.exclusionTargetRegions[
                    fieldName
                ].indexOf(targeting.id);
                if (index !== -1) {
                    newRegions = angular.copy(
                        entity.settings.exclusionTargetRegions
                    );
                    newRegions[fieldName].splice(index, 1);
                    entity.settings.exclusionTargetRegions = newRegions;
                }
                state.targetings = getTargetings();
                updateMessages();
            }

            function generateGeolocationObject(geolocation) {
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
                return {
                    id: geolocation.key,
                    section: constants.geolocationTypeText[geolocation.type],
                    name: geolocation.name,
                    title: geolocation.name,
                    badges: badges,
                    geolocation: geolocation,
                };
            }

            function fetchMappings() {
                var deferred = $q.defer();
                var unmappedKeys = extractGeotargetingKeysWithoutZips(
                    entity.settings.targetRegions
                )
                    .concat(
                        extractGeotargetingKeysWithoutZips(
                            entity.settings.exclusionTargetRegions
                        )
                    )
                    .filter(function(id) {
                        return !geolocationMappings[id];
                    });

                if (unmappedKeys.length > 0) {
                    var mappings = {};
                    zemGeoTargetingEndpoint
                        .map(unmappedKeys)
                        .then(function(response) {
                            response.forEach(function(geolocation) {
                                mappings[geolocation.key] = geolocation;
                            });
                            deferred.resolve(mappings);
                        });
                } else {
                    deferred.resolve({});
                }

                return deferred.promise;
            }

            // prettier-ignore
            function updateMessages() { // eslint-disable-line complexity
                var warnings = [];
                var infos = [];
                var regionsWithoutZips = extractGeotargetingKeysWithoutZips(
                    entity.settings.targetRegions
                );
                var exclusionRegionsWithoutZips = extractGeotargetingKeysWithoutZips(
                    entity.settings.exclusionTargetRegions
                );

                var i,
                    geolocation,
                    hasCountry = false,
                    hasOther = false;
                for (i = 0; i < regionsWithoutZips.length; i++) {
                    geolocation = geolocationMappings[regionsWithoutZips[i]];
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

                var outbrainNotSupported = function(id) {
                    var geolocation = geolocationMappings[id];
                    return !(geolocation && geolocation.outbrainId);
                };
                if (exclusionRegionsWithoutZips.length > 0) {
                    infos.push(INFO_OUTBRAIN_EXCLUDED);
                } else if (
                    regionsWithoutZips.length > 0 &&
                    regionsWithoutZips.every(outbrainNotSupported)
                ) {
                    infos.push(INFO_OUTBRAIN_INCLUDED);
                }

                var yahooNotSupported = function(id) {
                    return !geolocationMappings[id].woeid;
                };
                if (exclusionRegionsWithoutZips.some(yahooNotSupported)) {
                    infos.push(INFO_YAHOO_EXCLUDED);
                } else if (
                    regionsWithoutZips.length > 0 &&
                    regionsWithoutZips.every(yahooNotSupported)
                ) {
                    infos.push(INFO_YAHOO_INCLUDED);
                }

                state.messages.warnings = warnings;
                state.messages.infos = infos;
            }

            function extractGeotargetingKeysWithoutZips(targeting) {
                var keys = [];
                [FIELD_COUNTRY, FIELD_REGION, FIELD_CITY, FIELD_DMA].forEach(
                    function(geoTypeField) {
                        targeting[geoTypeField].forEach(function(key) {
                            keys.push(key);
                        });
                    }
                );
                return keys;
            }
        }
    });
