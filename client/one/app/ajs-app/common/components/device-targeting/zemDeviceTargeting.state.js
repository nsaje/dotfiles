angular
    .module('one.common')
    .service('zemDeviceTargetingStateService', function(
        $q,
        $http,
        zemPubSubService,
        zemDeviceTargetingConstants
    ) {
        //eslint-disable-line max-len
        var EVENTS = {
            ON_UPDATE: 'zemDeviceTargetingStateService_on-update',
        };

        function StateService(updateCallback) {
            var pubSub = zemPubSubService.createInstance();

            //
            // State Object
            //
            var state = {
                devices: [],
                placements: [],
                operatingSystems: [],
            };

            //
            // Public API
            //
            this.initialize = initialize;
            this.destroy = destroy;
            this.getState = getState;

            this.update = update;
            this.onUpdate = onUpdate;

            ///////////////////////////////////////////////////////////////////////////////////////////////
            // Internals
            //
            function initialize(targetDevices, targetPlacements, targetOs) {
                angular.extend(
                    state,
                    convertFromApi(targetDevices, targetPlacements, targetOs)
                );
            }

            function destroy() {
                pubSub.destroy();
            }

            function getState() {
                return state;
            }

            function update() {
                validate();
                updateSettings();
                pubSub.notify(EVENTS.ON_UPDATE, state);
            }

            function validate() {
                validateOperatingSystems();
            }

            function validateOperatingSystems() {
                state.operatingSystems.forEach(function validateVersions(
                    operatingSystem
                ) {
                    if (!operatingSystem.version) return;

                    var minVersionIdex = operatingSystem.versions.indexOf(
                        operatingSystem.version.min
                    );
                    var maxVersionIdex = operatingSystem.versions.indexOf(
                        operatingSystem.version.max
                    );
                    if (
                        minVersionIdex > 0 &&
                        maxVersionIdex > 0 &&
                        minVersionIdex > maxVersionIdex
                    ) {
                        operatingSystem.version.max =
                            operatingSystem.version.min;
                    }
                });
            }

            function updateSettings() {
                updateCallback(convertToApi(state));
            }

            ///////////////////////////////////////////////////////////////////////////////////////////////
            // Converters
            //
            function convertFromApi(targetDevices, targetPlacements, targetOs) {
                var data = {
                    devices: convertTargetDevicesFromApi(targetDevices),
                    placements: convertPlacementsFromApi(targetPlacements),
                    operatingSystems: convertOperatingSystemsFromApi(targetOs),
                };

                return data;
            }

            function convertToApi(state) {
                return {
                    targetDevices: convertTargetDevicesToApi(state.devices),
                    targetPlacements: convertPlacementsToApi(state.placements),
                    targetOs: convertOperatingSystemsToApi(
                        state.operatingSystems
                    ),
                };
            }

            function convertTargetDevicesFromApi(data) {
                if (!data) data = [];
                return zemDeviceTargetingConstants.DEVICES.map(function(item) {
                    return {
                        name: item.name,
                        value: item.value,
                        checked: data.indexOf(item.value) > -1,
                    };
                });
            }

            function convertTargetDevicesToApi(devices) {
                if (!devices) return [];
                return devices
                    .filter(function(item) {
                        return item.checked;
                    })
                    .map(function(item) {
                        return item.value;
                    });
            }

            function convertOperatingSystemsToApi(operatingSystems) {
                return operatingSystems.map(function(os) {
                    var osApi = {
                        name: os.value,
                    };

                    if (os.version) {
                        osApi.version = {};
                        if (os.version.min.value)
                            osApi.version.min = os.version.min.value;
                        if (os.version.max.value)
                            osApi.version.max = os.version.max.value;
                    }

                    return osApi;
                });
            }

            function convertOperatingSystemsFromApi(data) {
                if (!data) data = [];
                return data.map(function(targetOs) {
                    var option = angular.copy(findOs(targetOs.name));
                    if (option.versions) {
                        option.versions.unshift({value: null, name: ' - '});
                        option.version = {
                            min:
                                targetOs.version && targetOs.version.min
                                    ? findVersion(
                                          option.versions,
                                          targetOs.version.min
                                      )
                                    : option.versions[0],
                            max:
                                targetOs.version && targetOs.version.max
                                    ? findVersion(
                                          option.versions,
                                          targetOs.version.max
                                      )
                                    : option.versions[0],
                        };
                    }

                    return option;
                });

                function findOs(value) {
                    return zemDeviceTargetingConstants.OPERATING_SYSTEMS.filter(
                        function(os) {
                            return os.value === value;
                        }
                    )[0];
                }

                function findVersion(versions, value) {
                    return versions.filter(function(v) {
                        return v.value === value;
                    })[0];
                }
            }

            function convertPlacementsToApi(placements) {
                var data = placements
                    .filter(function(placement) {
                        return placement.selected;
                    })
                    .map(function(placement) {
                        return placement.value;
                    });

                if (data.length === placements.length || data.length === 0)
                    return [];

                return data;
            }

            function convertPlacementsFromApi(data) {
                if (!data) data = [];
                var placements = angular.copy(
                    zemDeviceTargetingConstants.PLACEMENTS
                );
                placements.forEach(function(placement) {
                    placement.selected =
                        data.length === 0 || data.indexOf(placement.value) >= 0;
                });

                return placements;
            }

            ///////////////////////////////////////////////////////////////////////////////////////////////
            // Events
            //
            function onUpdate(callback) {
                return pubSub.register(EVENTS.ON_UPDATE, callback);
            }
        }

        return {
            createInstance: function(updateCallback) {
                return new StateService(updateCallback);
            },
        };
    });
