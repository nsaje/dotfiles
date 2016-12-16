/* globals angular, constants */
/* eslint-disable camelcase */
'use strict';

angular.module('one.legacy').factory('zemUploadEndpointService', function ($http, $q, zemUploadApiConverter) {
    function UploadEndpoint (baseUrl) {

        this.upload = upload;
        this.createBatch = createBatch;

        this.save = save;
        this.cancel = cancel;

        this.getCandidates = getCandidates;
        this.checkStatus = checkStatus;
        this.addCandidate = addCandidate;
        this.updateCandidate = updateCandidate;
        this.removeCandidate = removeCandidate;

        function upload (data) {
            var deferred = $q.defer();
            var url = baseUrl + 'csv/';

            var formData = new FormData();
            formData.append('candidates', data.file);
            formData.append('batch_name', data.batchName ? data.batchName : '');

            $http.post(url, formData, {
                transformRequest: angular.identity,
                headers: {'Content-Type': undefined},
            }).success(function (data) {
                deferred.resolve({
                    batchId: data.data.batch_id,
                    batchName: data.data.batch_name,
                    candidates: zemUploadApiConverter.convertCandidatesFromApi(data.data.candidates),
                });
            }).error(function (data, status) {
                var result = {};
                if (status === '413') {
                    data = {
                        'data': {
                            'status': constants.uploadBatchStatus.FAILED,
                            'errors': {
                                'candidates': ['File too large (max 1MB).'],
                            },
                        },
                        'success': false,
                    };
                    result.errors = zemUploadApiConverter.convertValidationErrorsFromApi(data.data.errors);
                } else if (data && data.data && data.data.errors) {
                    result.errors = zemUploadApiConverter.convertValidationErrorsFromApi(data.data.errors);
                }

                deferred.reject(result);
            });

            return deferred.promise;
        }

        function createBatch (batchName) {
            var deferred = $q.defer();
            var url = baseUrl + 'batch/';
            var config = {
                params: {},
            };

            if (batchName) {
                config.batch_name = batchName;
            }

            $http.post(url, config).success(function (data) {
                deferred.resolve({
                    batchId: data.data.batch_id,
                    batchName: data.data.batch_name,
                    candidates: zemUploadApiConverter.convertCandidatesFromApi(data.data.candidates),
                });
            }).error(function (data) {
                var errors = null;
                if (data.data && data.data.errors) {
                    errors = zemUploadApiConverter.convertBatchErrorsFromApi(data.data.errors);
                }
                deferred.reject(errors);
            });

            return deferred.promise;
        }

        function checkStatus (batchId, candidates) {
            var deferred = $q.defer();
            var url = baseUrl + batchId + '/status/';
            var config = {
                params: {},
            };

            if (candidates) {
                config.params.candidates = candidates.join(',');
            }

            $http.get(url, config).
                success(function (data) {
                    var result = {
                        candidates: zemUploadApiConverter.convertStatusFromApi(data.data.candidates),
                    };
                    deferred.resolve(result);
                }).error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }

        function save (batchId, batchName) {
            var deferred = $q.defer();
            var url = baseUrl + batchId + '/save/';
            var data = {};

            if (batchName !== undefined) {
                data.batch_name = batchName;
            }

            $http.post(url, data).
                success(function (data) {
                    var result = {
                        numSuccessful: data.data.num_successful,
                        numErrors: data.data.num_errors,
                        errorReport: data.data.error_report,
                    };
                    deferred.resolve(result);
                }).error(function (data) {
                    var errors = null;
                    if (data.data && data.data.errors) {
                        errors = zemUploadApiConverter.convertBatchErrorsFromApi(data.data.errors);
                    }
                    deferred.reject(errors);
                });

            return deferred.promise;
        }

        function updateCandidate (batchId, candidate, defaults) {
            var deferred = $q.defer();
            var url = baseUrl + batchId + '/candidate_update/' + candidate.id + '/';

            var jsonData = {
                candidate: zemUploadApiConverter.convertPartialUpdateToApi(candidate),
                defaults: zemUploadApiConverter.convertDefaultFields(defaults),
            };

            var formData = new FormData();
            formData.append('data', angular.toJson(jsonData));
            if (candidate.hasOwnProperty('image')) {
                // handle file separately
                formData.append('image', candidate.image);
            }

            $http.post(url, formData, {
                transformRequest: angular.identity,
                headers: {'Content-Type': undefined},
            }).
                success(function (data) {
                    deferred.resolve({
                        updatedFields: zemUploadApiConverter.convertCandidateFieldsFromApi(data.data.updated_fields),
                        errors: zemUploadApiConverter.convertCandidateErrorsFromApi(data.data.errors),
                    });
                }).error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }

        function getCandidates (batchId) {
            var deferred = $q.defer();
            var url = baseUrl + batchId + '/candidate/';

            $http.get(url).
                success(function (result) {
                    deferred.resolve({
                        candidates: zemUploadApiConverter.convertCandidatesFromApi(result.data.candidates),
                    });
                }).error(function (result) {
                    deferred.reject(result);
                });

            return deferred.promise;
        }

        function addCandidate (batchId) {
            var deferred = $q.defer();
            var url = baseUrl + batchId + '/candidate/';

            $http.post(url).
                success(function (result) {
                    deferred.resolve({
                        candidate: zemUploadApiConverter.convertCandidateFromApi(result.data.candidate),
                    });
                }).error(function (result) {
                    deferred.reject(result);
                });

            return deferred.promise;
        }

        function removeCandidate (candidateId, batchId) {
            var deferred = $q.defer();
            var url = baseUrl + batchId + '/candidate/' + candidateId + '/';

            $http.delete(url).
                success(function () {
                    deferred.resolve();
                }).error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }

        function cancel (batchId) {
            var deferred = $q.defer();
            var url = batchId + '/cancel/';

            $http.post(url).success(deferred.resolve).error(deferred.reject);

            return deferred.promise;
        }
    }

    function getBaseUrl (adGroupId) {
        return '/api/ad_groups/' + adGroupId + '/contentads/upload/';
    }

    function createEndpoint (adGroupId) {
        var url = getBaseUrl(adGroupId);
        return new UploadEndpoint(url);
    }

    return {
        createEndpoint: createEndpoint,
    };
});
