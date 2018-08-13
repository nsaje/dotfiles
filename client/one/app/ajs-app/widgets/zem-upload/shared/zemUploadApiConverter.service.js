angular.module('one.widgets').service('zemUploadApiConverter', function() {
    this.convertCandidatesFromApi = convertCandidatesFromApi;
    this.convertValidationErrorsFromApi = convertValidationErrorsFromApi;
    this.convertBatchErrorsFromApi = convertBatchErrorsFromApi;
    this.convertStatusFromApi = convertStatusFromApi;
    this.convertPartialUpdateToApi = convertPartialUpdateToApi;
    this.convertDefaultFields = convertDefaultFields;

    this.convertCandidateErrorsFromApi = convertCandidateErrorsFromApi;
    this.convertCandidateFieldsFromApi = convertCandidateFieldsFromApi;
    this.convertCandidateFromApi = convertCandidateFromApi;

    function convertDefaultFields(defaults) {
        if (!defaults || !defaults.length) return [];

        var ret = [];
        if (defaults.indexOf('description') >= 0) {
            ret.push('description');
        }

        if (defaults.indexOf('imageCrop') >= 0) {
            ret.push('image_crop');
        }

        if (defaults.indexOf('brandName') >= 0) {
            ret.push('brand_name');
        }

        if (defaults.indexOf('callToAction') >= 0) {
            ret.push('call_to_action');
        }

        if (defaults.indexOf('displayUrl') >= 0) {
            ret.push('display_url');
        }
        return ret;
    }

    function convertPartialUpdateToApi(candidate) {
        return {
            id: candidate.id,
            label: candidate.label,
            url: candidate.url,
            title: candidate.title,
            image_url: candidate.imageUrl,
            image_crop: candidate.imageCrop,
            video_asset_id: candidate.videoAssetId,
            display_url: candidate.displayUrl,
            brand_name: candidate.brandName,
            description: candidate.description,
            call_to_action: candidate.callToAction,
            primary_tracker_url: candidate.primaryTrackerUrl,
            secondary_tracker_url: candidate.secondaryTrackerUrl,
        };
    }

    function removeUndefinedValues(obj) {
        Object.keys(obj).forEach(function(key) {
            if (obj[key] === undefined) {
                delete obj[key];
            }
        });
        return obj;
    }

    function convertCandidateErrorsFromApi(errors) {
        if (!errors) return {};

        return removeUndefinedValues({
            label: errors.label,
            title: errors.title,
            url: errors.url,
            image: errors.image,
            imageUrl: errors.image_url,
            imageCrop: errors.image_crop,
            videoAssetId: errors.video_asset_id,
            displayUrl: errors.display_url,
            brandName: errors.brand_name,
            description: errors.description,
            callToAction: errors.call_to_action,
            trackerUrls: errors.tracker_urls,
            primaryTrackerUrl: errors.primary_tracker_url,
            secondaryTrackerUrl: errors.secondary_tracker_url,
        });
    }

    function convertCandidateFieldsFromApi(candidate) {
        return removeUndefinedValues({
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
            videoAssetId: candidate.video_asset_id,
            hostedImageUrl: candidate.hosted_image_url,
            displayUrl: candidate.display_url,
            brandName: candidate.brand_name,
            description: candidate.description,
            callToAction: candidate.call_to_action,
            trackerUrls: candidate.tracker_urls,
            primaryTrackerUrl: candidate.primary_tracker_url,
            secondaryTrackerUrl: candidate.secondary_tracker_url,
        });
    }

    function convertCandidateFromApi(candidate) {
        var newCandidate = convertCandidateFieldsFromApi(candidate);
        newCandidate.errors = {};

        if (candidate.errors) {
            newCandidate.errors = convertCandidateErrorsFromApi(
                candidate.errors
            );
        }

        return removeUndefinedValues(newCandidate);
    }

    function convertCandidatesFromApi(candidates) {
        var result = [];
        angular.forEach(candidates, function(candidate) {
            result.push(convertCandidateFromApi(candidate));
        });
        return result;
    }

    function convertStatusFromApi(candidates) {
        var result = [];
        angular.forEach(candidates, function(candidate, candidateId) {
            result[candidateId] = convertCandidateFromApi(candidate);
        });
        return result;
    }

    function convertValidationErrorsFromApi(errors) {
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

    function convertBatchErrorsFromApi(errors) {
        return {
            batchName: errors.batch_name,
        };
    }
});
