import {AdGroup} from '../../../../core/entities/types/ad-group/ad-group';
import {
    TARGETING_CONNECTION_TYPE_OPTIONS,
    TARGETING_ENVIRONMENT_OPTIONS,
} from '../../entity-manager.config';
import {doesAnySettingHaveValue} from '../../helpers/entity.helpers';
import {ExpandableSection} from './ad-group-settings.drawer.constants';

export const EXPANDABLE_SECTIONS = [
    ExpandableSection.SCHEDULING,
    ExpandableSection.BUDGET,
    ExpandableSection.DEVICE_TARGETING,
    ExpandableSection.GEOTARGETING,
    ExpandableSection.AUDIENCE,
];

export const EXPANDED_SECTIONS_CONFIG: {
    [key in ExpandableSection]: (entity: AdGroup) => boolean;
} = {
    [ExpandableSection.SCHEDULING]: (entity: AdGroup): boolean => {
        return doesAnySettingHaveValue(entity.dayparting);
    },
    [ExpandableSection.BUDGET]: (entity: AdGroup): boolean => {
        return doesAnySettingHaveValue(
            entity.clickCappingDailyAdGroupMaxClicks,
            entity.frequencyCapping
        );
    },
    [ExpandableSection.DEVICE_TARGETING]: (entity: AdGroup): boolean => {
        return (
            doesAnySettingHaveValue(
                entity.targeting.os,
                entity.targeting.browsers?.included,
                entity.targeting.browsers?.excluded
            ) ||
            // has some options selected but not all options
            (entity.targeting.environments.length > 0 &&
                entity.targeting.environments.length !==
                    TARGETING_ENVIRONMENT_OPTIONS.length) ||
            (entity.targeting.connectionTypes.length > 0 &&
                entity.targeting.connectionTypes.length !==
                    TARGETING_CONNECTION_TYPE_OPTIONS.length)
        );
    },
    [ExpandableSection.GEOTARGETING]: (entity: AdGroup): boolean => {
        return doesAnySettingHaveValue(
            entity.targeting.geo.included.postalCodes,
            entity.targeting.geo.excluded.postalCodes
        );
    },
    [ExpandableSection.AUDIENCE]: (entity: AdGroup): boolean => {
        return doesAnySettingHaveValue(
            entity.targeting.customAudiences.included,
            entity.targeting.customAudiences.excluded,
            entity.targeting.retargetingAdGroups.included,
            entity.targeting.retargetingAdGroups.included,
            entity.targeting.audience
        );
    },
};
