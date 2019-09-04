/* eslint-disable camelcase */

angular
    .module('one.widgets')
    .factory('zemUploadEndpointService', function(
        $http,
        $q,
        zemUploadApiConverter,
        zemNavigationNewService
    ) {
        // eslint-disable-line max-len
        function UploadEndpoint(baseUrl, adGroupId) {
            var DIRECT_UPLOAD = 'DIRECT_UPLOAD';
            var VAST_UPLOAD = 'VAST_UPLOAD';
            var VAST_URL = 'VAST_URL';

            this.upload = upload;
            this.createBatch = createBatch;

            this.uploadVideo = uploadVideo;
            this.uploadVast = uploadVast;
            this.urlVast = urlVast;
            this.processVast = processVast;
            this.getVideoAsset = getVideoAsset;

            this.save = save;
            this.cancel = cancel;

            this.getCandidates = getCandidates;
            this.checkStatus = checkStatus;
            this.addCandidate = addCandidate;
            this.updateCandidate = updateCandidate;
            this.removeCandidate = removeCandidate;

            function upload(data) {
                var deferred = $q.defer();
                var url = baseUrl + 'csv/';

                var formData = new FormData();
                formData.append('candidates', data.file);
                formData.append(
                    'batch_name',
                    data.batchName ? data.batchName : ''
                );
                formData.append(
                    'account_id',
                    zemNavigationNewService.getActiveAccount().id
                );
                formData.append('ad_group_id', adGroupId);

                $http
                    .post(url, formData, {
                        transformRequest: angular.identity,
                        headers: {'Content-Type': undefined},
                    })
                    .success(function(data) {
                        deferred.resolve({
                            batchId: data.data.batch_id,
                            batchName: data.data.batch_name,
                            candidates: zemUploadApiConverter.convertCandidatesFromApi(
                                data.data.candidates
                            ),
                        });
                    })
                    .error(function(data, status) {
                        var result = {};
                        if (status === '413') {
                            data = {
                                data: {
                                    status: constants.uploadBatchStatus.FAILED,
                                    errors: {
                                        candidates: [
                                            'File too large (max 1MB).',
                                        ],
                                    },
                                },
                                success: false,
                            };
                            result.errors = zemUploadApiConverter.convertValidationErrorsFromApi(
                                data.data.errors
                            );
                        } else if (data && data.data && data.data.errors) {
                            result.errors = zemUploadApiConverter.convertValidationErrorsFromApi(
                                data.data.errors
                            );
                        }

                        deferred.reject(result);
                    });

                return deferred.promise;
            }

            function createBatch(batchName, withoutCandidates) {
                var deferred = $q.defer();
                var url = baseUrl + 'batch/';
                var config = {};
                if (withoutCandidates) {
                    config.params = {};
                    config.params.withoutCandidates = true;
                }
                var data = {
                    account_id: zemNavigationNewService.getActiveAccount().id,
                    ad_group_id: adGroupId,
                };

                if (batchName) {
                    data.batch_name = batchName;
                }

                $http
                    .post(url, data, config)
                    .success(function(data) {
                        deferred.resolve({
                            batchId: data.data.batch_id,
                            batchName: data.data.batch_name,
                            candidates: zemUploadApiConverter.convertCandidatesFromApi(
                                data.data.candidates
                            ),
                        });
                    })
                    .error(function(data) {
                        var errors = null;
                        if (data && data.data && data.data.errors) {
                            errors = zemUploadApiConverter.convertBatchErrorsFromApi(
                                data.data.errors
                            );
                        }
                        deferred.reject(errors);
                    });

                return deferred.promise;
            }

            function uploadVideo(file, progressEventHandler) {
                return createVideoAsset(DIRECT_UPLOAD, file.name, '').then(
                    function(videoAsset) {
                        return uploadToS3(
                            file,
                            videoAsset,
                            'application/octet-stream',
                            progressEventHandler
                        );
                    }
                );
            }

            function uploadVast(file, progressEventHandler) {
                return createVideoAsset(VAST_UPLOAD, file.name, '').then(
                    function(videoAsset) {
                        return uploadToS3(
                            file,
                            videoAsset,
                            'text/xml',
                            progressEventHandler
                        );
                    }
                );
            }

            function urlVast(url) {
                return createVideoAsset(VAST_URL, '', url);
            }

            function processVast(videoAsset) {
                return updateVideoAsset(videoAsset.id, {
                    status: constants.videoAssetStatus.PROCESSING,
                });
            }

            function createVideoAsset(type, name, vasturl) {
                var deferred = $q.defer();
                var url =
                    '/rest/v1/accounts/' +
                    zemNavigationNewService.getActiveAccount().id +
                    '/videoassets/';
                var data = {
                    name: name,
                    vastUrl: vasturl,
                    upload: {
                        type: type,
                    },
                };

                $http
                    .post(url, data)
                    .then(function(data) {
                        deferred.resolve(data.data.data);
                    })
                    .catch(function(error) {
                        deferred.reject(error);
                    });

                return deferred.promise;
            }

            function uploadToS3(
                file,
                videoAsset,
                contentType,
                progressEventHandler
            ) {
                var config = {
                    headers: {'Content-Type': contentType},
                    uploadEventHandlers: {
                        progress: progressEventHandler,
                    },
                };
                var deferred = $q.defer();
                $http
                    .put(videoAsset.upload.url, file, config)
                    .then(function() {
                        deferred.resolve(videoAsset);
                    })
                    .catch(function() {
                        deferred.reject();
                    });
                return deferred.promise;
            }

            function getVideoAsset(id) {
                var deferred = $q.defer();
                var url =
                    '/rest/v1/accounts/' +
                    zemNavigationNewService.getActiveAccount().id +
                    '/videoassets/' +
                    id;

                $http
                    .get(url)
                    .then(function(data) {
                        deferred.resolve(data.data.data);
                    })
                    .catch(function(error) {
                        deferred.reject(error);
                    });

                return deferred.promise;
            }

            function updateVideoAsset(id, input) {
                var deferred = $q.defer();
                var url =
                    '/rest/v1/accounts/' +
                    zemNavigationNewService.getActiveAccount().id +
                    '/videoassets/' +
                    id;

                $http
                    .put(url, input)
                    .then(function(data) {
                        deferred.resolve(data.data.data);
                    })
                    .catch(function(error) {
                        deferred.reject(error);
                    });

                return deferred.promise;
            }

            function checkStatus(batchId, candidates) {
                var deferred = $q.defer();
                var url = baseUrl + batchId + '/status/';
                var config = {
                    params: {},
                };

                if (candidates) {
                    config.params.candidates = candidates.join(',');
                }

                $http
                    .get(url, config)
                    .success(function(data) {
                        var result = {
                            candidates: zemUploadApiConverter.convertStatusFromApi(
                                data.data.candidates
                            ),
                        };
                        deferred.resolve(result);
                    })
                    .error(function(data) {
                        deferred.reject(data);
                    });

                return deferred.promise;
            }

            function save(batchId, batchName) {
                var deferred = $q.defer();
                var url = baseUrl + batchId + '/save/';
                var data = {};

                if (batchName !== undefined) {
                    data.batch_name = batchName;
                }

                $http
                    .post(url, data)
                    .success(function(data) {
                        var result = {
                            numSuccessful: data.data.num_successful,
                            numErrors: data.data.num_errors,
                            errorReport: data.data.error_report,
                        };
                        deferred.resolve(result);
                    })
                    .error(function(data) {
                        var errors = null;
                        if (data.data && data.data.errors) {
                            errors = zemUploadApiConverter.convertBatchErrorsFromApi(
                                data.data.errors
                            );
                        }
                        deferred.reject(errors);
                    });

                return deferred.promise;
            }

            function updateCandidate(batchId, candidate, defaults) {
                var deferred = $q.defer();
                var url =
                    baseUrl +
                    batchId +
                    '/candidate_update/' +
                    candidate.id +
                    '/';

                var jsonData = {
                    candidate: zemUploadApiConverter.convertPartialUpdateToApi(
                        candidate
                    ),
                    defaults: zemUploadApiConverter.convertDefaultFields(
                        defaults
                    ),
                };

                var formData = new FormData();
                formData.append('data', angular.toJson(jsonData));
                if (candidate.hasOwnProperty('image')) {
                    // handle file separately
                    formData.append('image', candidate.image);
                }
                if (candidate.hasOwnProperty('icon')) {
                    formData.append('icon', candidate.icon);
                }

                $http
                    .post(url, formData, {
                        transformRequest: angular.identity,
                        headers: {'Content-Type': undefined},
                    })
                    .success(function(data) {
                        deferred.resolve({
                            updatedFields: zemUploadApiConverter.convertCandidateFieldsFromApi(
                                data.data.updated_fields
                            ),
                            errors: zemUploadApiConverter.convertCandidateErrorsFromApi(
                                data.data.errors
                            ),
                        });
                    })
                    .error(function(data) {
                        deferred.reject(data);
                    });

                return deferred.promise;
            }

            function getCandidates(batchId) {
                var deferred = $q.defer();
                var url = baseUrl + batchId + '/candidate/';

                $http
                    .get(url)
                    .success(function(result) {
                        deferred.resolve({
                            candidates: zemUploadApiConverter.convertCandidatesFromApi(
                                result.data.candidates
                            ),
                        });
                    })
                    .error(function(result) {
                        deferred.reject(result);
                    });

                return deferred.promise;
            }

            function addCandidate(batchId) {
                var deferred = $q.defer();
                var url = baseUrl + batchId + '/candidate/';

                $http
                    .post(url)
                    .success(function(result) {
                        deferred.resolve({
                            candidate: zemUploadApiConverter.convertCandidateFromApi(
                                result.data.candidate
                            ),
                        });
                    })
                    .error(function(result) {
                        deferred.reject(result);
                    });

                return deferred.promise;
            }

            function removeCandidate(candidateId, batchId) {
                var deferred = $q.defer();
                var url = baseUrl + batchId + '/candidate/' + candidateId + '/';

                $http
                    .delete(url)
                    .success(function() {
                        deferred.resolve();
                    })
                    .error(function(data) {
                        deferred.reject(data);
                    });

                return deferred.promise;
            }

            function cancel(batchId) {
                var deferred = $q.defer();
                var url = batchId + '/cancel/';

                $http
                    .post(url)
                    .success(deferred.resolve)
                    .error(deferred.reject);

                return deferred.promise;
            }
        }

        function createEndpoint(adGroupId) {
            var url = '/api/contentads/upload/';
            return new UploadEndpoint(url, adGroupId);
        }

        return {
            createEndpoint: createEndpoint,
        };
    });
