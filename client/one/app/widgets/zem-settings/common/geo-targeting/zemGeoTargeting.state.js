angular.module('one.widgets').service('zemGeoTargetingStateService', function (zemGeoTargetingEndpoint, $q) {
    this.createInstance = createInstance;

    var TOOLTIP_NOT_SUPPORTED_BY_OUTBRAIN = 'Not supported by Outbrain';
    var TOOLTIP_NOT_SUPPORTED_BY_YAHOO = 'Not supported by Yahoo!';
    var TOOLTIP_NOT_SUPPORTED_BY_FACEBOOK = 'Not supported by Facebook';
    var WARNING_DIFFERENT_LOCATION_LEVELS = 'You are using different geographical features (city, country, ...). Note that if for example both the country United States and the city of New York are included, the whole US will be targeted.'; // eslint-disable-line max-len
    var INFO_OUTBRAIN_EXCLUDED = 'Outbrain media source will be paused because it doesn\'t support excluded locations.'; // eslint-disable-line max-len
    var INFO_OUTBRAIN_INCLUDED = 'Outbrain media source will be paused because it doesn\'t support any of the included locations.'; // eslint-disable-line max-len
    var INFO_YAHOO_EXCLUDED = 'Yahoo media source will be paused because it doesn\'t support all the excluded locations.'; // eslint-disable-line max-len
    var INFO_YAHOO_INCLUDED = 'Yahoo media source will be paused because it doesn\'t support any of the included locations.'; // eslint-disable-line max-len
    var INFO_FACEBOOK_EXCLUDED = 'Facebook media source will be paused because it doesn\'t support excluded locations.';
    var INFO_FACEBOOK_INCLUDED = 'Facebook media source will be paused because it doesn\'t support any of the included locations.'; // eslint-disable-line max-len

    function createInstance (entity) {
        return new zemGeoTargetingStateService(entity);
    }

    function zemGeoTargetingStateService (entity) {
        this.getState = getState;
        this.init = init;
        this.refresh = refresh;
        this.addTargeting = addTargeting;
        this.removeTargeting = removeTargeting;

        var state = {
            targetings: [],
            messages: {
                warnings: [],
                infos: [],
            },
        };

        var geolocationMappings = {};

        function getState () {
            return state;
        }

        function init () {
            fetchMappings().then(function (mappings) {
                geolocationMappings = mappings;
                state.targetings = getEnabledTargetings();
                updateMessages();
            });
        }

        function getEnabledTargetings () {
            var isIncluded;
            var isExcluded;
            var geolocation;
            var targetings = [];

            entity.settings.targetRegions.forEach(function (key) {
                isIncluded = true;
                isExcluded = false;
                geolocation = geolocationMappings[key];
                if (geolocation) {
                    targetings.push(generateGeolocationObject(geolocation, isIncluded, isExcluded));
                }
            });
            entity.settings.exclusionTargetRegions.forEach(function (key) {
                isIncluded = false;
                isExcluded = true;
                geolocation = geolocationMappings[key];
                if (geolocation) {
                    targetings.push(generateGeolocationObject(geolocation, isIncluded, isExcluded));
                }
            });

            targetings.sort(function (a, b) {
                var ORDER = [
                    constants.geolocationType.COUNTRY,
                    constants.geolocationType.REGION,
                    constants.geolocationType.DMA,
                    constants.geolocationType.CITY
                ];
                return ORDER.indexOf(a.geolocation.type) - ORDER.indexOf(b.geolocation.type);
            });

            return targetings;
        }

        function refresh (searchTerm) {
            var targetings = getEnabledTargetings();
            if (searchTerm.length < 2) {
                state.targetings = targetings;
                return;
            }
            zemGeoTargetingEndpoint.search(searchTerm).then(function (response) {
                var SECTION_RESULTS_SIZE = 10;
                var sectionItems = {};
                response.forEach(function (geolocation) {
                    for (var i = 0; i < targetings.length; i++) {
                        if (targetings[i].id === geolocation.key) {
                            return;
                        }
                    }
                    sectionItems[geolocation.type] = sectionItems[geolocation.type] || 0;
                    if (sectionItems[geolocation.type] < SECTION_RESULTS_SIZE) {
                        sectionItems[geolocation.type]++;
                        var isIncluded = false;
                        var isExcluded = false;
                        targetings.push(generateGeolocationObject(geolocation, isIncluded, isExcluded));
                    }
                });
                state.targetings = targetings;
            });
        }

        function addTargeting (targeting) {
            if (targeting.included) {
                if (!entity.settings.targetRegions) {
                    entity.settings.targetRegions = [];
                }
                entity.settings.targetRegions = entity.settings.targetRegions.concat(targeting.id);
            }

            if (targeting.excluded) {
                if (!entity.settings.exclusionTargetRegions) {
                    entity.settings.exclusionTargetRegions = [];
                }
                entity.settings.exclusionTargetRegions = entity.settings.exclusionTargetRegions.concat(targeting.id);
            }

            geolocationMappings[targeting.id] = targeting.geolocation;
            state.targetings = getEnabledTargetings();
            updateMessages();
        }

        function removeTargeting (targeting) {
            var index = entity.settings.targetRegions.indexOf(targeting.id);
            if (index >= 0) {
                entity.settings.targetRegions = entity.settings.targetRegions.slice(0, index)
                    .concat(entity.settings.targetRegions.slice(index + 1));
            }

            index = entity.settings.exclusionTargetRegions.indexOf(targeting.id);
            if (index >= 0) {
                entity.settings.exclusionTargetRegions = entity.settings.exclusionTargetRegions.slice(0, index)
                    .concat(entity.settings.exclusionTargetRegions.slice(index + 1));
            }
            state.targetings = getEnabledTargetings();
            updateMessages();
        }

        function generateGeolocationObject (geolocation, included, excluded) {
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
            if (!geolocation.facebookKey) {
                badges.push({
                    class: 'facebook',
                    text: TOOLTIP_NOT_SUPPORTED_BY_FACEBOOK,
                });
            }
            return {
                id: geolocation.key,
                section: constants.geolocationTypeText[geolocation.type],
                name: geolocation.name,
                title: geolocation.name,
                badges: badges,
                included: included,
                excluded: excluded,
                geolocation: geolocation,
            };
        }

        function fetchMappings () {
            var deferred = $q.defer();
            var unmappedKeys = entity.settings.targetRegions
                .concat(entity.settings.exclusionTargetRegions)
                .filter(isNotZip)
                .filter(function (id) {
                    return !geolocationMappings[id];
                });

            if (unmappedKeys.length > 0) {
                var mappings = {};
                zemGeoTargetingEndpoint.map(unmappedKeys).then(function (response) {
                    response.forEach(function (geolocation) {
                        mappings[geolocation.key] = geolocation;
                    });
                    deferred.resolve(mappings);
                });
            } else {
                deferred.resolve({});
            }

            return deferred.promise;
        }

        function updateMessages () {
            var warnings = [];
            var infos = [];
            var regionsWithoutZips = entity.settings.targetRegions.filter(isNotZip);
            var exclusionRegionsWithoutZips = entity.settings.exclusionTargetRegions.filter(isNotZip);

            var i, geolocation, hasCountry = false, hasOther = false;
            for (i = 0; i < regionsWithoutZips.length; i++) {
                geolocation = geolocationMappings[regionsWithoutZips[i]];
                if (geolocation && geolocation.type === constants.geolocationType.COUNTRY) {
                    hasCountry = true;
                } else {
                    hasOther = true;
                }
            }
            if (hasCountry && hasOther) {
                warnings.push(WARNING_DIFFERENT_LOCATION_LEVELS);
            }

            var outbrainNotSupported = function (id) {
                return !geolocationMappings[id].outbrainId;
            };
            if (exclusionRegionsWithoutZips.length > 0) {
                infos.push(INFO_OUTBRAIN_EXCLUDED);
            } else if (regionsWithoutZips.length > 0 && regionsWithoutZips.every(outbrainNotSupported)) {
                infos.push(INFO_OUTBRAIN_INCLUDED);
            }

            var yahooNotSupported = function (id) {
                return !geolocationMappings[id].woeid;
            };
            if (exclusionRegionsWithoutZips.some(yahooNotSupported)) {
                infos.push(INFO_YAHOO_EXCLUDED);
            } else if (regionsWithoutZips.length > 0 && regionsWithoutZips.every(yahooNotSupported)) {
                infos.push(INFO_YAHOO_INCLUDED);
            }

            var facebookNotSupported = function (id) {
                return !geolocationMappings[id].facebookKey;
            };
            if (exclusionRegionsWithoutZips.length > 0) {
                infos.push(INFO_FACEBOOK_EXCLUDED);
            } else if (regionsWithoutZips.length > 0 && regionsWithoutZips.every(facebookNotSupported)) {
                infos.push(INFO_FACEBOOK_INCLUDED);
            }

            state.messages.warnings = warnings;
            state.messages.infos = infos;
        }

        function isNotZip (id) {
            return id.indexOf(':') === -1;
        }
    }
});
