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
        var item = {
            id: candidate.id,
            label: candidate.label,
            url: candidate.url,
            title: candidate.title,
            image_url: candidate.imageUrl,
            image_crop: candidate.imageCrop,
            icon_url: candidate.iconUrl,
            type: convertAdTypeToApi(candidate.adType),
            ad_tag: candidate.adTag,
            video_asset_id: candidate.videoAssetId,
            display_url: candidate.displayUrl,
            brand_name: candidate.brandName,
            description: candidate.description,
            call_to_action: candidate.callToAction,
            primary_tracker_url: candidate.primaryTrackerUrl,
            secondary_tracker_url: candidate.secondaryTrackerUrl,
            trackers: candidate.trackers
                ? candidate.trackers.map(function(tracker) {
                      return {
                          event_type: tracker.eventType
                              ? tracker.eventType.toLowerCase()
                              : null,
                          method: tracker.method
                              ? tracker.method.toLowerCase()
                              : null,
                          url: tracker.url,
                          fallback_url: tracker.fallbackUrl,
                          tracker_optional: tracker.trackerOptional,
                      };
                  })
                : undefined,
        };

        if (candidate.adSize) {
            var adSize = options.adSizes.find(function(size) {
                return size.value === candidate.adSize;
            });
            if (adSize) {
                item.image_width = adSize.width;
                item.image_height = adSize.height;
            }
        }

        return item;
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
            icon: errors.icon,
            iconUrl: errors.icon_url,
            adType: errors.type,
            adSize: getAdSizeErrors(errors.image_width, errors.image_height),
            adTag: errors.ad_tag,
            videoAssetId: errors.video_asset_id,
            displayUrl: errors.display_url,
            brandName: errors.brand_name,
            description: errors.description,
            callToAction: errors.call_to_action,
            trackerUrls: errors.tracker_urls,
            primaryTrackerUrl: errors.primary_tracker_url,
            secondaryTrackerUrl: errors.secondary_tracker_url,
            trackers: errors.trackers
                ? JSON.parse(errors.trackers).map(function(trackerError) {
                      return {
                          eventType: trackerError.event_type,
                          method: trackerError.method,
                          url: trackerError.url,
                          fallbackUrl: trackerError.fallback_url,
                      };
                  })
                : undefined,
        });
    }

    function convertCandidateFieldsFromApi(candidate) {
        return removeUndefinedValues({
            id: candidate.id,
            label: candidate.label,
            url: candidate.url,
            title: candidate.title,
            imageStatus: candidate.image_status,
            iconStatus: candidate.icon_status,
            urlStatus: candidate.url_status,
            imageUrl: candidate.image_url,
            imageId: candidate.image_id,
            imageHash: candidate.image_hash,
            imageWidth: candidate.image_width,
            imageHeight: candidate.image_height,
            imageCrop: candidate.image_crop,
            iconUrl: candidate.icon_url,
            iconId: candidate.icon_id,
            iconHash: candidate.icon_hash,
            iconWidth: candidate.icon_width,
            iconHeight: candidate.icon_height,
            adType: convertAdTypeFromApi(candidate.type),
            adSize: getAdSize(candidate.image_width, candidate.image_height),
            adTag: candidate.ad_tag,
            videoAssetId: candidate.video_asset_id,
            hostedImageUrl: candidate.hosted_image_url,
            hostedIconUrl: candidate.hosted_icon_url,
            landscapeHostedImageUrl: candidate.landscape_hosted_image_url,
            portraitHostedImageUrl: candidate.portrait_hosted_image_url,
            displayHostedImageUrl: candidate.display_hosted_image_url,
            displayUrl: candidate.display_url,
            brandName: candidate.brand_name,
            description: candidate.description,
            callToAction: candidate.call_to_action,
            trackerUrls: candidate.tracker_urls,
            primaryTrackerUrl: candidate.primary_tracker_url,
            secondaryTrackerUrl: candidate.secondary_tracker_url,
            primaryTrackerUrlStatus: candidate.primary_tracker_url_status,
            secondaryTrackerUrlStatus: candidate.secondary_tracker_url_status,
            trackers: candidate.trackers
                ? candidate.trackers.map(function(tracker) {
                      return {
                          eventType: tracker.event_type
                              ? tracker.event_type.toUpperCase()
                              : null,
                          method: tracker.method
                              ? tracker.method.toUpperCase()
                              : null,
                          url: tracker.url,
                          fallbackUrl: tracker.fallback_url,
                          trackerOptional: tracker.tracker_optional,
                      };
                  })
                : undefined,
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
        angular.forEach(candidates, function(candidate) {
            result.push(convertCandidateFromApi(candidate));
        });
        return result;
    }

    function convertValidationErrorsFromApi(errors) {
        var converted = {
            file: errors.candidates,
            batchName: errors.batch_name,
            displayUrl: errors.display_url,
            adType: errors.type,
            adSize: getAdSizeErrors(errors.image_width, errors.image_height),
            adTag: errors.ad_tag,
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

    function getAdSize(imageWidth, imageHeight) {
        if (imageWidth && imageHeight) {
            var adSize = options.adSizes.find(function(size) {
                return size.width === imageWidth && size.height === imageHeight;
            });
            if (adSize) {
                return adSize.value;
            }
        }
        return undefined;
    }

    function getAdSizeErrors(errorsImageWidth, errorsImageHeight) {
        if (errorsImageWidth || errorsImageHeight) {
            return ['Missing ad size.'];
        }
    }

    function convertAdTypeFromApi(apiAdType) {
        if (!apiAdType) {
            return undefined;
        }
        var uiAdType = options.adTypes.find(function(x) {
            return x.legacyValue === apiAdType;
        });
        return uiAdType && uiAdType.value;
    }

    function convertAdTypeToApi(uiAdType) {
        if (!uiAdType) {
            return undefined;
        }
        var apiAdType = options.adTypes.find(function(x) {
            return x.value === uiAdType;
        });
        return apiAdType && apiAdType.legacyValue;
    }
});
