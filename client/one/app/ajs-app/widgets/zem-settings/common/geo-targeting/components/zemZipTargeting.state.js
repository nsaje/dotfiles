angular
    .module('one.widgets')
    .service('zemZipTargetingStateService', function(zemGeoTargetingEndpoint) {
        this.createInstance = createInstance;

        var FIELD_ZIP = 'postalCodes';
        var FIELD_COUNTRY = 'countries';

        function createInstance(entity) {
            return new zemZipTargetingStateService(entity);
        }

        function zemZipTargetingStateService(entity) {
            this.getState = getState;
            this.init = init;
            this.updateState = updateState;
            this.checkConstraints = checkConstraints;
            this.searchCountries = searchCountries;
            this.cleanUserInput = cleanUserInput;

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

            function getState() {
                return state;
            }

            function init() {
                var zipsToDisplay = initTypeAndZipsToDisplay();
                if (!zipsToDisplay) {
                    return;
                }
                initCountryAndTextarea(zipsToDisplay);
                checkConstraints();
            }

            function initTypeAndZipsToDisplay() {
                var zipsToDisplay;
                var inclusionZips =
                    entity.settings.targetRegions[FIELD_ZIP] || [];
                var exclusionZips =
                    entity.settings.exclusionTargetRegions[FIELD_ZIP] || [];
                if (exclusionZips.length) {
                    state.zipTargetingType = constants.zipTargetingType.EXCLUDE;
                    zipsToDisplay = exclusionZips;
                    if (inclusionZips.length) {
                        setAPIOnlySettingsBlocker();
                        return;
                    }
                } else {
                    state.zipTargetingType = constants.zipTargetingType.INCLUDE;
                    zipsToDisplay = inclusionZips;
                }
                return zipsToDisplay;
            }

            function initCountryAndTextarea(zipsToDisplay) {
                if (!zipsToDisplay.length) {
                    setCountry('US');
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

            function updateState() {
                updateEntity();
                checkConstraints();
            }

            function updateEntity() {
                var zipCodes = textToZipList(state.textareaContent);
                var countryCode = state.selectedCountry.key;
                var zipsWithCountries = zipCodes.map(function(zipCode) {
                    return countryCode + ':' + zipCode;
                });
                var newRegionsIncluded = angular.copy(
                    entity.settings.targetRegions
                );
                newRegionsIncluded[FIELD_ZIP] = [];
                var newRegionsExcluded = angular.copy(
                    entity.settings.exclusionTargetRegions
                );
                newRegionsExcluded[FIELD_ZIP] = [];
                if (
                    state.zipTargetingType ===
                    constants.zipTargetingType.INCLUDE
                ) {
                    newRegionsIncluded[FIELD_ZIP] = zipsWithCountries;
                } else {
                    newRegionsExcluded[FIELD_ZIP] = zipsWithCountries;
                }
                entity.settings.targetRegions = newRegionsIncluded;
                entity.settings.exclusionTargetRegions = newRegionsExcluded;
            }

            function checkConstraints() {
                var isSelectedCountry = function(key) {
                    return key === state.selectedCountry.key;
                };
                var includedCountries =
                    entity.settings.targetRegions[FIELD_COUNTRY] || [];
                var excludedCountries =
                    entity.settings.exclusionTargetRegions[FIELD_COUNTRY] || [];
                var countryIncluded = includedCountries.filter(
                    isSelectedCountry
                )[0];
                var countryExcluded = excludedCountries.filter(
                    isSelectedCountry
                )[0];
                state.blockers.countryIncluded = false;
                if (countryIncluded || countryExcluded) {
                    state.blockers.countryIncluded = true;
                }
            }

            function cleanUserInput() {
                state.textareaContent = textToZipList(
                    state.textareaContent
                ).join(', ');
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
