/* globals angular, constants */
/* eslint-disable camelcase */
'use strict';

angular.module('one.legacy').factory('zemUploadEndpointService', ['$http', '$q', function ($http, $q) {
    function UploadEndpoint (baseUrl) {

        this.upload = function (data) {
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
                    candidates: convertCandidatesFromApi(data.data.candidates),
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
                    result.errors = convertValidationErrorsFromApi(data.data.errors);
                } else if (data && data.data && data.data.errors) {
                    result.errors = convertValidationErrorsFromApi(data.data.errors);
                }

                deferred.reject(result);
            });

            return deferred.promise;
        };

        this.createBatch = function (batchName) {
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
                    candidates: convertCandidatesFromApi(data.data.candidates),
                });
            }).error(function (data) {
                var errors = null;
                if (data.data && data.data.errors) {
                    errors = convertBatchErrorsFromApi(data.data.errors);
                }
                deferred.reject(errors);
            });

            return deferred.promise;
        };

        this.checkStatus = function (batchId, candidates) {
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
                        candidates: convertStatusFromApi(data.data.candidates),
                    };
                    deferred.resolve(result);
                }).error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.save = function (batchId, batchName) {
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
                        errors = convertBatchErrorsFromApi(data.data.errors);
                    }
                    deferred.reject(errors);
                });

            return deferred.promise;
        };

        this.updateCandidate = function (candidate, batchId) {
            var deferred = $q.defer();
            var url = baseUrl + batchId + '/candidate/' + candidate.id + '/';

            var config = {
                params: {},
            };

            var data = {
                candidate: convertCandidateToApi(candidate),
                defaults: getDefaultFields(candidate),
            };

            $http.put(url, data, config).
                success(function (data) {
                    deferred.resolve({
                        candidates: convertCandidatesFromApi(data.data.candidates),
                    });
                }).error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.updateCandidatePartial = function (batchId, candidate) {
            var deferred = $q.defer();
            var url = baseUrl + batchId + '/candidate_update/' + candidate.id + '/';

            var config = {
                params: {},
            };

            var data = {
                candidate: convertCandidateToApi(candidate),
            };

            $http.put(url, data, config).
                success(function (data) {
                    deferred.resolve({
                        errors: convertCandidateErrorsFromApi(data.data.errors),
                    });
                }).error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.getCandidates = function (batchId) {
            var deferred = $q.defer();
            var url = baseUrl + batchId + '/candidate/';

            $http.get(url).
                success(function (result) {
                    deferred.resolve({
                        candidates: convertCandidatesFromApi(result.data.candidates),
                    });
                }).error(function (result) {
                    deferred.reject(result);
                });

            return deferred.promise;
        };

        this.addCandidate = function (batchId) {
            var deferred = $q.defer();
            var url = baseUrl + batchId + '/candidate/';

            $http.post(url).
                success(function (result) {
                    deferred.resolve({
                        candidate: convertCandidateFromApi(result.data.candidate),
                    });
                }).error(function (result) {
                    deferred.reject(result);
                });

            return deferred.promise;
        };

        this.removeCandidate = function (candidateId, batchId) {
            var deferred = $q.defer();
            var url = baseUrl + batchId + '/candidate/' + candidateId + '/';

            $http.delete(url).
                success(function () {
                    deferred.resolve();
                }).error(function (data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        };

        this.cancel = function (batchId) {
            var deferred = $q.defer();
            var url = batchId + '/cancel/';

            $http.post(url).success(deferred.resolve).error(deferred.reject);

            return deferred.promise;
        };


        function getDefaultFields (candidate) {
            var ret = [];

            if (!candidate.defaults) {
                return ret;
            }

            if (candidate.defaults.description) {
                ret.push('description');
            }

            if (candidate.defaults.imageCrop) {
                ret.push('image_crop');
            }

            if (candidate.defaults.brandName) {
                ret.push('brand_name');
            }

            if (candidate.defaults.callToAction) {
                ret.push('call_to_action');
            }

            if (candidate.defaults.displayUrl) {
                ret.push('display_url');
            }

            return ret;
        }

        function convertCandidateToApi (candidate) {
            var ret = {
                id: candidate.id,
                label: candidate.label,
                url: candidate.url,
                title: candidate.title,
                image_url: candidate.imageUrl,
                image_crop: candidate.imageCrop,
                display_url: candidate.displayUrl,
                brand_name: candidate.brandName,
                description: candidate.description,
                call_to_action: candidate.callToAction,
            };

            if (candidate.useTrackers) {
                ret.primary_tracker_url = candidate.primaryTrackerUrl;
                ret.secondary_tracker_url = candidate.secondaryTrackerUrl;
            }

            return ret;
        }

        function convertCandidateErrorsFromApi (errors) {
            if (!errors) return {};

            return {
                label: errors.label,
                title: errors.title,
                url: errors.url,
                imageUrl: errors.image_url,
                imageCrop: errors.image_crop,
                displayUrl: errors.display_url,
                brandName: errors.brand_name,
                description: errors.description,
                callToAction: errors.call_to_action,
                trackerUrls: errors.tracker_urls,
                primaryTrackerUrl: errors.primary_tracker_url,
                secondaryTrackerUrl: errors.secondary_tracker_url,
            };
        }

        function convertCandidateFromApi (candidate) {
            return {
                id: candidate.id,
                label: candidate.label,
                url: candidate.url,
                title: candidate.title,
                imageStatus: candidate.image_status,
                urlStatus: candidate.url_status,
                imageUrl: candidate.image_url,
                imageId: candidate.image_id,
                imageHash: candidate.image_hash,
                imageWidth: candidate.image_width,
                imageHeight: candidate.image_height,
                imageCrop: candidate.image_crop,
                hostedImageUrl: candidate.hosted_image_url,
                displayUrl: candidate.display_url,
                brandName: candidate.brand_name,
                description: candidate.description,
                callToAction: candidate.call_to_action,
                trackerUrls: candidate.tracker_urls,
                primaryTrackerUrl: candidate.primary_tracker_url,
                secondaryTrackerUrl: candidate.secondary_tracker_url,
                errors: convertCandidateErrorsFromApi(candidate.errors),
            };
        }

        function convertCandidatesFromApi (candidates) {
            var result = [];
            angular.forEach(candidates, function (candidate) {
                result.push(convertCandidateFromApi(candidate));
            });
            return result;
        }

        function convertStatusFromApi (candidates) {
            var result = [];
            angular.forEach(candidates, function (candidate, candidateId) {
                result[candidateId] = convertCandidateFromApi(candidate);
            });
            return result;
        }

        function convertValidationErrorsFromApi (errors) {
            var converted = {
                file: errors.candidates,
                batchName: errors.batch_name,
                displayUrl: errors.display_url,
                brandName: errors.brand_name,
                description: errors.description,
                callToAction: errors.call_to_action,
            };

            if (errors.details) {
                converted.details = {
                    reportUrl: errors.details && errors.details.report_url,
                    description: errors.details && errors.details.description,
                };
            }

            return converted;
        }

        function convertBatchErrorsFromApi (errors) {
            return {
                batchName: errors.batch_name,
            };
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
}]);
