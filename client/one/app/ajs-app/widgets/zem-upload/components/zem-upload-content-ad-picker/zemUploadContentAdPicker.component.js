angular.module('one.widgets').component('zemUploadContentAdPicker', {
    bindings: {
        endpoint: '=',
        batchId: '=',
        batchName: '=',
        candidates: '=',
        isEdit: '=?',
        showVideoUpload: '=?',
        showDisplayUpload: '=?',
        adPickerApi: '=?',
        editFormApi: '=?',
        statusUpdatedCallback: '=?',
    },
    template: require('./zemUploadContentAdPicker.component.html'),
    controller: function($window, $interval) {
        var $ctrl = this;

        $ctrl.isCandidateStatusLoading = isCandidateStatusLoading;
        $ctrl.isCandidateStatusOk = isCandidateStatusOk;
        $ctrl.isCandidateStatusError = isCandidateStatusError;
        $ctrl.startPollingVideoAssetStatus = startPollingVideoAssetStatus;
        $ctrl.addCandidate = addCandidate;
        $ctrl.removeCandidate = removeCandidate;
        $ctrl.getContentErrorsMsg = getContentErrorsMsg;
        $ctrl.getImageErrorsMsg = getImageErrorsMsg;
        $ctrl.download = download;
        $ctrl.updateCandidateCallback = updateCandidateCallback;
        $ctrl.refreshCandidatesCallback = refreshCandidatesCallback;
        $ctrl.adType = constants.adType;

        $ctrl.$onInit = function() {
            $ctrl.editFormApi = $ctrl.editFormApi || {};
            $ctrl.titlePlaceholder = $ctrl.showDisplayUpload
                ? 'Ad Name'
                : 'Ad Title';

            if ($ctrl.adPickerApi) {
                $ctrl.adPickerApi.getWaitingCandidateIds = getWaitingCandidateIds;
                $ctrl.adPickerApi.isVideoAssetBeingProcessed = isVideoAssetBeingProcessed;
                $ctrl.adPickerApi.isVideoAssetProcessingErrorPresent = isVideoAssetProcessingErrorPresent;
                $ctrl.adPickerApi.hasErrors = hasErrors;
            }

            startPolling();
        };

        $ctrl.$onDestroy = function() {
            stopPolling();
            stopPollingAllVideoAssetsStatuses();
        };

        $ctrl.getAdSize = function(candidate) {
            if (candidate.imageWidth && candidate.imageHeight) {
                return candidate.imageWidth + 'x' + candidate.imageHeight;
            }
            return '';
        };

        $ctrl.toggleEditForm = function(candidate, event) {
            event.stopPropagation();
            if (
                $ctrl.editFormApi.selectedId &&
                $ctrl.editFormApi.selectedId === candidate.id
            ) {
                $ctrl.editFormApi.close(candidate);
            } else {
                $ctrl.editFormApi.open(candidate);
            }
        };

        function isCandidateStatusLoading(candidate) {
            var asyncUploadJobStatus = getAsyncUploadJobStatus(candidate);
            return (
                asyncUploadJobStatus ===
                    constants.contentAdCandidateStatus.LOADING ||
                isVideoAssetBeingProcessed(candidate)
            );
        }

        function isCandidateStatusOk(candidate) {
            if (isCandidateStatusLoading(candidate)) return false;

            var response =
                getAsyncUploadJobStatus(candidate) ===
                constants.contentAdCandidateStatus.OK;
            if (isVideoAssetPresent(candidate)) {
                response = response && isVideoAssetReadyForUse(candidate);
            }
            return response;
        }

        function isCandidateStatusError(candidate) {
            if (isCandidateStatusLoading(candidate)) return false;

            var asyncUploadJobStatus = getAsyncUploadJobStatus(candidate);
            return (
                asyncUploadJobStatus ===
                    constants.contentAdCandidateStatus.ERRORS ||
                isVideoAssetProcessingErrorPresent(candidate)
            );
        }

        // eslint-disable-next-line complexity
        function getAsyncUploadJobStatus(candidate) {
            if (
                candidate.imageStatus ===
                    constants.asyncUploadJobStatus.PENDING_START &&
                candidate.urlStatus ===
                    constants.asyncUploadJobStatus.PENDING_START
            ) {
                // newly added candidate
                return null;
            }

            if (
                candidate.imageStatus ===
                    constants.asyncUploadJobStatus.WAITING_RESPONSE ||
                candidate.urlStatus ===
                    constants.asyncUploadJobStatus.WAITING_RESPONSE
            ) {
                return constants.contentAdCandidateStatus.LOADING;
            }

            if (hasErrors(candidate)) {
                return constants.contentAdCandidateStatus.ERRORS;
            }

            if (
                (candidate.imageStatus ===
                    constants.asyncUploadJobStatus.PENDING_START &&
                    candidate.adType !== constants.adType.AD_TAG) ||
                candidate.urlStatus ===
                    constants.asyncUploadJobStatus.PENDING_START
            ) {
                // important to check this after checking for errors
                return null;
            }

            return constants.contentAdCandidateStatus.OK;
        }

        function isVideoAssetPresent(candidate) {
            return (
                candidate.videoAsset &&
                candidate.videoAsset.status !==
                    constants.videoAssetStatus.INITIALIZED
            );
        }

        function isVideoAssetBeingProcessed(candidate) {
            return (
                isVideoAssetPresent(candidate) &&
                !isVideoAssetReadyForUse(candidate) &&
                !isVideoAssetProcessingErrorPresent(candidate)
            );
        }

        function isVideoAssetReadyForUse(candidate) {
            return (
                isVideoAssetPresent(candidate) &&
                candidate.videoAsset.status ===
                    constants.videoAssetStatus.READY_FOR_USE
            );
        }

        function isVideoAssetProcessingErrorPresent(candidate) {
            return (
                isVideoAssetPresent(candidate) &&
                candidate.videoAsset.status ===
                    constants.videoAssetStatus.PROCESSING_ERROR
            );
        }

        function getWaitingCandidateIds() {
            var ret = $ctrl.candidates
                .filter(function(candidate) {
                    if (
                        getAsyncUploadJobStatus(candidate) ===
                        constants.contentAdCandidateStatus.LOADING
                    ) {
                        return true;
                    }
                    return false;
                })
                .map(function(candidate) {
                    return candidate.id;
                });
            return ret;
        }

        var pollInterval = null;

        function startPolling() {
            if (pollInterval !== null) {
                return;
            }

            pollInterval = $interval(function() {
                var waitingCandidates = getWaitingCandidateIds();
                if (!waitingCandidates.length) {
                    stopPolling();
                    return;
                }
                $ctrl.endpoint
                    .checkStatus($ctrl.batchId, waitingCandidates)
                    .then(function(data) {
                        updateCandidatesStatuses(data.candidates);
                        refreshCandidates(data.candidates);
                    });
            }, 2500);
        }

        function stopPolling() {
            if (pollInterval !== null) {
                $interval.cancel(pollInterval);
                pollInterval = null;
            }
        }

        function startPollingVideoAssetStatus(candidate) {
            if (candidate.videoAssetStatusPollerInterval) return;
            candidate.videoAssetStatusPollerInterval = $interval(function() {
                videoAssetStatusPoller(candidate);
            }, 2000);
        }

        function stopPollingVideoAssetStatus(candidate) {
            if (candidate && candidate.videoAssetStatusPollerInterval) {
                $interval.cancel(candidate.videoAssetStatusPollerInterval);
                candidate.videoAssetStatusPollerInterval = null;
            }
        }

        function stopPollingAllVideoAssetsStatuses() {
            $ctrl.candidates.forEach(function(candidate) {
                stopPollingVideoAssetStatus(candidate);
            });
        }

        function videoAssetStatusPoller(candidate) {
            $ctrl.endpoint
                .getVideoAsset(candidate.videoAssetId)
                .then(function(asset) {
                    candidate.videoAsset = asset;
                    if (!isVideoAssetBeingProcessed(candidate)) {
                        stopPollingVideoAssetStatus(candidate);
                    }
                });
        }

        function hasErrors(candidate) {
            for (var key in candidate.errors) {
                if (
                    candidate.errors.hasOwnProperty(key) &&
                    candidate.errors[key]
                ) {
                    return true;
                }
            }

            return false;
        }

        function updateCandidatesStatuses(updatedCandidates) {
            angular.forEach(updatedCandidates, function(updatedCandidate) {
                var candidate = $ctrl.candidates.filter(function(candidate) {
                    if (candidate.id === updatedCandidate.id) return true;
                })[0];

                if (!candidate) return;

                if (
                    updatedCandidate.imageStatus !==
                    constants.asyncUploadJobStatus.PENDING_START
                ) {
                    candidate.imageStatus = updatedCandidate.imageStatus;
                    if (updatedCandidate.errors.hasOwnProperty('imageUrl')) {
                        candidate.errors.imageUrl =
                            updatedCandidate.errors.imageUrl;
                    }
                    if (updatedCandidate.hasOwnProperty('hostedImageUrl')) {
                        candidate.hostedImageUrl =
                            updatedCandidate.hostedImageUrl;
                    }
                }

                if (
                    updatedCandidate.urlStatus !==
                    constants.asyncUploadJobStatus.PENDING_START
                ) {
                    candidate.urlStatus = updatedCandidate.urlStatus;
                    if (updatedCandidate.errors.hasOwnProperty('url')) {
                        candidate.errors.url = updatedCandidate.errors.url;
                    }
                }
            });
            if ($ctrl.statusUpdatedCallback) {
                $ctrl.statusUpdatedCallback();
            }
        }

        function refreshCandidates(updatedCandidates, fields) {
            // fields parameter can be used to only selectively update fields and their error messages
            // If not specified, it updates all fields.
            // Example: use as default button in edit form
            angular.forEach(updatedCandidates, function(updatedCandidate) {
                var candidate = $ctrl.candidates.filter(function(candidate) {
                    if (candidate.id === updatedCandidate.id) return true;
                })[0];

                if (!candidate) {
                    return;
                }

                Object.keys(updatedCandidate).forEach(function(field) {
                    if (field === 'errors') return;
                    if (fields && fields.length && fields.indexOf(field) < 0)
                        return;
                    candidate[field] = updatedCandidate[field];
                });

                if (!fields || !fields.length) {
                    candidate.errors = updatedCandidate.errors;
                    return;
                }

                fields.forEach(function(field) {
                    delete candidate.errors[field];
                    if (updatedCandidate.errors[field])
                        candidate.errors[field] =
                            updatedCandidate.errors[field];
                });
            });
        }

        function addCandidate() {
            $ctrl.addCandidateRequestInProgress = true;
            $ctrl.addCandidateRequestFailed = false;

            $ctrl.endpoint
                .addCandidate($ctrl.batchId)
                .then(
                    function(data) {
                        $ctrl.candidates.push(data.candidate);
                        $ctrl.editFormApi.open(data.candidate);
                        if ($ctrl.statusUpdatedCallback) {
                            $ctrl.statusUpdatedCallback();
                        }
                    },
                    function() {
                        $ctrl.addCandidateRequestFailed = true;
                    }
                )
                .finally(function() {
                    $ctrl.addCandidateRequestInProgress = false;
                });
        }

        function removeCandidate(candidate, event) {
            event.stopPropagation(); // the whole row has ng-click registered

            candidate.removeRequestInProgress = true;
            candidate.removeRequestFailed = false;

            stopPollingVideoAssetStatus(candidate);

            if (
                $ctrl.editFormApi &&
                $ctrl.editFormApi.selectedId === candidate.id
            ) {
                $ctrl.editFormApi.close();
            }

            $ctrl.endpoint
                .removeCandidate(candidate.id, $ctrl.batchId)
                .then(
                    function() {
                        $ctrl.candidates = $ctrl.candidates.filter(function(
                            el
                        ) {
                            return candidate.id !== el.id;
                        });
                        if ($ctrl.statusUpdatedCallback) {
                            $ctrl.statusUpdatedCallback();
                        }
                    },
                    function() {
                        candidate.removeRequestFailed = true;
                    }
                )
                .finally(function() {
                    candidate.removeRequestInProgress = false;
                });
        }

        function getContentErrorsMsg(candidate) {
            if (!candidate.errors) {
                return '';
            }

            var errs = [];
            angular.forEach(candidate.errors, function(error, key) {
                if (key !== 'imageUrl') {
                    Array.prototype.push.apply(errs, error);
                }
            });

            if (errs.length < 2) {
                return errs[0] || '';
            }

            return errs.length + ' content errors';
        }

        function getImageErrorsMsg(candidate) {
            if (!candidate.errors || !candidate.errors.imageUrl) {
                return '';
            }

            var errs = candidate.errors.imageUrl;
            if (errs.length < 2) {
                return errs[0] || '';
            }

            return errs.length + ' image errors';
        }

        function download() {
            var url =
                '/api/contentads/upload/' +
                $ctrl.batchId +
                '/download/?batch_name=' +
                encodeURIComponent($ctrl.batchName);
            $window.open(url, '_blank');
        }

        function updateCandidateCallback(fields) {
            $ctrl.endpoint.getCandidates($ctrl.batchId).then(function(result) {
                updateCandidatesStatuses(result.candidates);
                if (fields && fields.length)
                    refreshCandidates(result.candidates, fields);
                startPolling();
            });
        }

        function refreshCandidatesCallback() {
            return $ctrl.endpoint
                .getCandidates($ctrl.batchId)
                .then(function(result) {
                    refreshCandidates(result.candidates);
                    startPolling();
                });
        }
    },
});
