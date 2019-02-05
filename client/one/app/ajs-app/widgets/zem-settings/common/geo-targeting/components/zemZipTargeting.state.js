angular
    .module('one.widgets')
    .service('zemZipTargetingStateService', function(zemGeoTargetingEndpoint) {
        this.createInstance = createInstance;

        var FIELD_ZIP = 'postalCodes';
        var FIELD_COUNTRY = 'countries';

        function createInstance(propagateUpdate) {
            return new zemZipTargetingStateService(propagateUpdate);
        }

        function zemZipTargetingStateService(propagateUpdate) {
            this.getState = getState;
            this.updateTargeting = updateTargeting;
            this.setTargeting = setTargeting;
            this.searchCountries = searchCountries;

            var state = {
                zipTargetingType: '',
                selectedCountry: '',
                textareaContent: '',
                countrySearchResults: [],
                blockers: {
                    apiOnlySettings: false,
                    countryIncluded: false,
                },
            };

            var includedLocations;
            var excludedLocations;

            function getState() {
                return state;
            }

            function updateTargeting(included, excluded) {
                includedLocations = included;
                excludedLocations = excluded;

                var zipsToDisplay = initTypeAndZipsToDisplay(
                    includedLocations,
                    excludedLocations
                );
                if (!zipsToDisplay) {
                    return;
                }
                initCountryAndTextarea(zipsToDisplay);
                checkConstraints();
            }

            function initTypeAndZipsToDisplay(
                includedLocations,
                excludedLocations
            ) {
                var zipsToDisplay = [];
                var inclusionZips = includedLocations[FIELD_ZIP] || [];
                var exclusionZips = excludedLocations[FIELD_ZIP] || [];

                if (!state.zipTargetingType) {
                    state.zipTargetingType = constants.zipTargetingType.INCLUDE;
                }

                if (exclusionZips.length) {
                    state.zipTargetingType = constants.zipTargetingType.EXCLUDE;
                    zipsToDisplay = exclusionZips;
                    if (inclusionZips.length) {
                        setAPIOnlySettingsBlocker();
                        return;
                    }
                } else if (inclusionZips.length) {
                    state.zipTargetingType = constants.zipTargetingType.INCLUDE;
                    zipsToDisplay = inclusionZips;
                }
                return zipsToDisplay;
            }

            function initCountryAndTextarea(zipsToDisplay) {
                if (!zipsToDisplay.length) {
                    state.textareaContent = '';
                    if (!state.selectedCountry) {
                        setCountry('US');
                    }
                } else {
                    var countryCode = getCountryCode(zipsToDisplay[0]);
                    setCountry(countryCode);

                    var zipCodes = [];
                    zipsToDisplay.forEach(function(zipWithCountryCode) {
                        if (zipWithCountryCode.indexOf(countryCode) !== 0) {
                            setAPIOnlySettingsBlocker();
                            return;
                        }
                        zipCodes.push(getZipCode(zipWithCountryCode));
                    });
                    state.textareaContent = zipCodes.join(', ');
                }
            }

            function setAPIOnlySettingsBlocker() {
                state.blockers.apiOnlySettings = true;
            }

            function searchCountries(searchTerm) {
                if (searchTerm.length < 1) {
                    state.countrySearchResults = [];
                    return;
                }
                zemGeoTargetingEndpoint
                    .searchByTypes(searchTerm, [
                        constants.geolocationType.COUNTRY,
                    ])
                    .then(function(result) {
                        state.countrySearchResults = result;
                    });
            }

            function setTargeting() {
                var zipCodes = textToZipList(state.textareaContent);
                var countryCode = state.selectedCountry.key;
                var zipsWithCountries = zipCodes.map(function(zipCode) {
                    return countryCode + ':' + zipCode;
                });

                var updatedIncludedLocations = angular.copy(includedLocations);
                updatedIncludedLocations[FIELD_ZIP] = [];

                var updatedExcludedLocations = angular.copy(excludedLocations);
                updatedExcludedLocations[FIELD_ZIP] = [];

                if (
                    state.zipTargetingType ===
                    constants.zipTargetingType.INCLUDE
                ) {
                    updatedIncludedLocations[FIELD_ZIP] = zipsWithCountries;
                } else {
                    updatedExcludedLocations[FIELD_ZIP] = zipsWithCountries;
                }

                propagateUpdate({
                    includedLocations: updatedIncludedLocations,
                    excludedLocations: updatedExcludedLocations,
                });
            }

            function checkConstraints() {
                state.blockers.countryIncluded = false;

                if (
                    state.zipTargetingType ===
                    constants.zipTargetingType.EXCLUDE
                ) {
                    return;
                }

                var isSelectedCountry = function(key) {
                    return key === state.selectedCountry.key;
                };
                var includedCountries = includedLocations[FIELD_COUNTRY] || [];
                var excludedCountries = excludedLocations[FIELD_COUNTRY] || [];
                var countryIncluded = includedCountries.filter(
                    isSelectedCountry
                )[0];
                var countryExcluded = excludedCountries.filter(
                    isSelectedCountry
                )[0];
                if (countryIncluded || countryExcluded) {
                    state.blockers.countryIncluded = true;
                }
            }

            function textToZipList(text) {
                return text
                    .trim()
                    .split(/\s*[,\n]+\s*/)
                    .filter(function(zip) {
                        return zip;
                    });
            }

            function setCountry(key) {
                if (
                    state.selectedCountry &&
                    state.selectedCountry.key === key
                ) {
                    return;
                }
                state.selectedCountry = {key: key}; // we set the key first and fill in the name asynchronously
                zemGeoTargetingEndpoint.mapKey(key).then(function(result) {
                    state.selectedCountry = result;
                });
            }

            function getCountryCode(zipWithCountryCode) {
                return zipWithCountryCode.split(':')[0];
            }

            function getZipCode(zipWithCountryCode) {
                return zipWithCountryCode.split(':')[1];
            }
        }
    });
