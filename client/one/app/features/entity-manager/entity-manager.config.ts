import {EntityType} from '../../app.constants';

export const ENTITY_MANAGER_CONFIG = {
    settingsQueryParam: 'settings',
    idStateParam: 'id',
    levelStateParam: 'level',
    levelToEntityTypeMap: {
        account: EntityType.ACCOUNT,
        campaign: EntityType.CAMPAIGN,
        adgroup: EntityType.AD_GROUP,
    },
    maxCampaignConversionGoals: 15,
};
