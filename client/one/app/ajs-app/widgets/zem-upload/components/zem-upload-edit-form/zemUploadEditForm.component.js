var callToAction = require('../../zemUpload.config').callToAction;

angular.module('one.widgets').directive('zemUploadEditForm', function() {
    // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        bindToController: {
            api: '=',
            endpoint: '=',
            refreshCallback: '=',
            updateCallback: '=',
            startPollingVideoAssetStatus: '=',
            batchId: '=',
            isEdit: '=',
            showVideoUpload: '=',
            showDisplayUpload: '=',
        },
        controllerAs: 'ctrl',
        template: require('./zemUploadEditForm.component.html'),
        link: function(scope, element, attrs, ctrl) {
            ctrl.scrollTop = function() {
                element[0].scrollTop = 0;
            };
        },
        controller: 'ZemUploadEditFormCtrl',
    };
});

angular
    .module('one.widgets')
    .controller('ZemUploadEditFormCtrl', function(
        config,
        $q,
        $timeout,
        $scope,
        zemAuthStore
    ) {
        // eslint-disable-line max-len
        var vm = this;
        vm.config = config;

        vm.NUM_PARTIAL_UPDATE_RETRIES = 5;

        vm.MAX_URL_LENGTH = 936;
        vm.MAX_TITLE_LENGTH = 90;
        vm.MAX_DESCRIPTION_LENGTH = 150;
        vm.MAX_DISPLAY_URL_LENGTH = 35;
        vm.MAX_BRAND_NAME_LENGTH = 25;
        vm.MAX_CALL_TO_ACTION_LENGTH = 25;
        vm.MAX_LABEL_LENGTH = 256;

        vm.videoAssetStatus = constants.videoAssetStatus;
        vm.hasPermission = zemAuthStore.hasPermission.bind(zemAuthStore);

        vm.adType = constants.adType;
        vm.adSizes = options.adSizes;
        vm.imageCrops = options.imageCrops;
        vm.videoTypeOptions = options.videoTypes;
        vm.videoTypes = constants.videoType;
        vm.callToActionOptions = callToAction;
        vm.candidateStatuses = constants.contentAdCandidateStatus;
        vm.fieldsLoading = {};
        vm.fieldsSaved = {};
        vm.fieldsApiErrors = {};

        // content ad picker API
        vm.api.selectedId = null;
        vm.api.open = open;
        vm.api.close = refreshAndClose;

        vm.showDesktop = true;
        vm.nativeAdPreviewConfig = {showMobilePortraitAd: true};

        function open(candidate) {
            vm.requestFailed = false;
            vm.selectedCandidate = candidate;
            vm.selectedCandidate.defaults = {};
            vm.selectedCandidate.usePrimaryTracker = !!vm.selectedCandidate
                .primaryTrackerUrl;
            vm.selectedCandidate.useSecondaryTracker = !!vm.selectedCandidate
                .secondaryTrackerUrl;
            vm.scrollTop();
            vm.api.selectedId = candidate.id;
            vm.showImageUpload = vm.isEdit || !vm.selectedCandidate.imageUrl;
            vm.showIconUpload = vm.isEdit || !vm.selectedCandidate.iconUrl;
            vm.fieldsLoading = {};
            vm.fieldsSaved = {};
            vm.fieldsApiErrors = {};

            if (!candidate.trackers) {
                candidate.trackers = [];
            }

            if (vm.showVideoUpload) {
                handleVideoCreatives();
            } else if (vm.showDisplayUpload) {
                handleDisplayCreatives();
            } else {
                handleNativeCreatives();
            }

            if (vm.isEdit && vm.selectedCandidate.videoAssetId) {
                vm.startPollingVideoAssetStatus(candidate);
            }
            if (!vm.selectedCandidate.videoAsset) {
                vm.selectedCandidate.videoAsset = {
                    type: constants.videoType.DIRECT_UPLOAD,
                    status: constants.videoAssetStatus.INITIALIZED,
                };
            }
        }

        function handleVideoCreatives() {
            vm.adTypes = filterAdTypes(
                [constants.campaignTypes.VIDEO],
                options.adTypes
            );
            if (!vm.isEdit) {
                validateAndResetAdType(
                    [constants.campaignTypes.VIDEO],
                    constants.adType.VIDEO
                );
            }
        }

        function handleDisplayCreatives() {
            vm.adTypes = filterAdTypes(
                [constants.campaignTypes.DISPLAY],
                options.adTypes
            );
            if (!vm.isEdit) {
                validateAndResetAdType(
                    [constants.campaignTypes.DISPLAY],
                    constants.adType.IMAGE
                );
            }
        }

        function handleNativeCreatives() {
            vm.adTypes = filterAdTypes(
                [
                    constants.campaignTypes.CONTENT,
                    constants.campaignTypes.CONVERSION,
                    constants.campaignTypes.MOBILE,
                ],
                options.adTypes
            );
            if (!vm.isEdit) {
                validateAndResetAdType(
                    [
                        constants.campaignTypes.CONTENT,
                        constants.campaignTypes.CONVERSION,
                        constants.campaignTypes.MOBILE,
                    ],
                    constants.adType.CONTENT
                );
            }
        }

        function filterAdTypes(campaignTypes, adTypes) {
            return angular.copy(adTypes).filter(function(adType) {
                return campaignTypes.some(function(x) {
                    return adType.campaignTypes.indexOf(x) >= 0;
                });
            });
        }

        function validateAndResetAdType(campaignTypes, defaultAdType) {
            var adType = options.adTypes.find(function(adType) {
                var found = false;
                if (adType.value === vm.selectedCandidate.adType) {
                    found = campaignTypes.some(function(x) {
                        return adType.campaignTypes.indexOf(x) >= 0;
                    });
                }
                return found;
            });
            if (!adType) {
                vm.selectedCandidate.adType = defaultAdType;
                vm.updateField(vm.selectedCandidate, 'adType');
            }
        }

        function refreshAndClose() {
            var promise = vm.refreshCallback();
            close();
            return promise;
        }

        function close() {
            vm.api.selectedId = null;
            vm.selectedCandidate = null;
        }

        function refreshSelectedCandidateFields(field, updatedFields, errors) {
            // multiple fields can be updated as a result of initiang update of a single one
            // so refresh all returned fields
            delete vm.selectedCandidate.errors[field];
            Object.keys(updatedFields).forEach(function(updatedField) {
                vm.selectedCandidate[updatedField] =
                    updatedFields[updatedField];
                delete vm.selectedCandidate.errors[updatedField];
            });
            angular.forEach(errors, function(error, key) {
                vm.selectedCandidate.errors[key] = error;
            });
        }

        vm.imageUploadCallback = function(file) {
            vm.selectedCandidate.image = file;
            vm.updateField(vm.selectedCandidate, 'image');
            $scope.$digest();
        };

        vm.iconUploadCallback = function(file) {
            vm.selectedCandidate.icon = file;
            vm.updateField(vm.selectedCandidate, 'icon');
            $scope.$digest();
        };

        vm.updateField = function(candidate, field, useAsDefault) {
            var selectedId = candidate.id;
            var defaults = [];
            if (useAsDefault && !vm.isEdit) defaults.push(field);

            var data = {
                id: candidate.id,
            };
            data[field] = candidate[field];

            vm.fieldsSaved[field] = false;
            vm.fieldsLoading[field] = true;
            vm.fieldsApiErrors[field] = false;

            var retries = 0;
            var persistUpdate = function() {
                vm.endpoint
                    .updateCandidate(vm.batchId, data, defaults)
                    .then(function(data) {
                        vm.updateCallback(defaults);
                        if (
                            !vm.selectedCandidate ||
                            selectedId !== vm.selectedCandidate.id
                        ) {
                            // edit form closed or selection changed in the mean time
                            return;
                        }

                        refreshSelectedCandidateFields(
                            field,
                            data.updatedFields,
                            data.errors
                        );
                        vm.fieldsSaved[field] = true;
                        vm.fieldsLoading[field] = false;
                    })
                    .catch(function() {
                        if (++retries === vm.NUM_PARTIAL_UPDATE_RETRIES) {
                            vm.fieldsApiErrors[field] = true;
                            vm.fieldsLoading[field] = false;
                            return;
                        }

                        $timeout(function() {
                            persistUpdate();
                        }, 5000);
                    });
            };

            persistUpdate();
        };

        vm.addPrimaryTracker = function(candidate) {
            vm.fieldsSaved.primaryTrackerUrl = false;
            candidate.usePrimaryTracker = true;
        };

        vm.removePrimaryTracker = function(candidate) {
            candidate.usePrimaryTracker = false;
            candidate.primaryTrackerUrl = null;
            vm.updateField(candidate, 'primaryTrackerUrl');
        };

        vm.addSecondaryTracker = function(candidate) {
            vm.fieldsSaved.secondaryTrackerUrl = false;
            candidate.useSecondaryTracker = true;
        };

        vm.removeSecondaryTracker = function(candidate) {
            candidate.useSecondaryTracker = false;
            candidate.secondaryTrackerUrl = null;
            vm.updateField(candidate, 'secondaryTrackerUrl');
        };

        vm.saveTrackers = function(candidate, trackers) {
            candidate.trackers = trackers;
            vm.updateField(candidate, 'trackers');
        };

        vm.fieldsHaveErrors = function(fields) {
            if (typeof fields === 'string') fields = [fields];
            for (var i = 0; i < fields.length; i++) {
                if (
                    vm.selectedCandidate.errors[fields[i]] ||
                    vm.fieldsApiErrors[fields[i]]
                ) {
                    return true;
                }
            }
            return false;
        };

        vm.toggleImageUpload = function() {
            if (vm.isEdit) return;
            vm.fieldsSaved.image = false;
            vm.fieldsSaved.imageUrl = false;
            vm.showImageUpload = !vm.showImageUpload;
        };

        vm.toggleIconUpload = function() {
            if (vm.isEdit) return;
            vm.fieldsSaved.icon = false;
            vm.fieldsSaved.iconUrl = false;
            vm.showIconUpload = !vm.showIconUpload;
        };

        vm.callToActionSelect2Config = {
            dropdownCssClass: 'service-fee-select2',
            createSearchChoice: function(term, data) {
                if (
                    $(data).filter(function() {
                        return this.text.localeCompare(term) === 0;
                    }).length === 0
                ) {
                    return {id: term, text: term};
                }
            },
            data: callToAction,
        };

        vm.videoUploadCallback = function(file) {
            // Save reference to the candidate to which video is uploaded to be available in async closures
            var candidate = vm.selectedCandidate;
            candidate.videoUploadProgress = 0;
            candidate.videoAsset.status =
                constants.videoAssetStatus.NOT_UPLOADED;

            vm.fieldsApiErrors.videoAssetId = false;

            vm.endpoint
                .uploadVideo(file, function updateUploadProgress(event) {
                    candidate.videoUploadProgress = Math.round(
                        (event.loaded / event.total) * 100
                    );
                })
                .then(function(videoAsset) {
                    candidate.videoAsset = videoAsset;
                    candidate.videoAssetId = videoAsset.id;
                    vm.updateField(candidate, 'videoAssetId');
                    vm.startPollingVideoAssetStatus(candidate);
                })
                .catch(function() {
                    vm.fieldsApiErrors.videoAssetId = true;
                    candidate.videoAsset.status =
                        constants.videoAssetStatus.INITIALIZED;
                });
        };

        vm.vastUploadCallback = function(file) {
            var candidate = vm.selectedCandidate;
            (candidate.videoAsset.status =
                constants.videoAssetStatus.NOT_UPLOADED),
                vm.endpoint
                    .uploadVast(file, function updateUploadProgress(event) {
                        candidate.videoUploadProgress = Math.round(
                            (event.loaded / event.total) * 100
                        );
                    })
                    .then(function(videoAsset) {
                        candidate.videoAsset.status =
                            constants.videoAssetStatus.PROCESSING;
                        return vm.endpoint
                            .processVast(videoAsset)
                            .then(function(videoAsset) {
                                candidate.videoAsset = videoAsset;
                                candidate.videoAssetId = videoAsset.id;
                                vm.updateField(candidate, 'videoAssetId');
                            });
                    })
                    .catch(function() {
                        vm.fieldsApiErrors.videoAssetId = true;
                        candidate.videoAsset.status =
                            constants.videoAssetStatus.INITIALIZED;
                    });
        };

        vm.vastUrlCallback = function(url) {
            var candidate = vm.selectedCandidate;
            candidate.videoAsset.status =
                constants.videoAssetStatus.NOT_UPLOADED;

            vm.fieldsSaved.vastUrl = false;
            vm.fieldsLoading.vastUrl = true;
            vm.fieldsApiErrors.vastUrl = false;

            vm.endpoint
                .urlVast(url)
                .then(function(videoAsset) {
                    if (
                        !vm.selectedCandidate ||
                        candidate.id !== vm.selectedCandidate.id
                    ) {
                        // edit form closed or selection changed in the mean time
                        return;
                    }

                    vm.fieldsSaved.vastUrl = true;
                    vm.fieldsLoading.vastUrl = false;
                    delete vm.selectedCandidate.errors.vastUrl;

                    candidate.videoAsset = videoAsset;
                    candidate.videoAssetId = videoAsset.id;
                    vm.updateField(candidate, 'videoAssetId');
                })
                .catch(function(data) {
                    if (
                        !vm.selectedCandidate ||
                        candidate.id !== vm.selectedCandidate.id
                    ) {
                        // edit form closed or selection changed in the mean time
                        return;
                    }

                    vm.fieldsLoading.vastUrl = false;
                    vm.fieldsApiErrors.vastUrl = true;
                    vm.selectedCandidate.errors.vastUrl = data.data.details;

                    candidate.videoAsset.status =
                        constants.videoAssetStatus.INITIALIZED;
                });
        };
    });
