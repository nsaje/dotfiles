import {EntityType} from '../../../app.constants';
import * as commonHelpers from '../../../shared/helpers/common.helpers';

export function getAdminLink(entityType: EntityType, entityId: string): string {
    let entity;
    if (entityType === EntityType.ACCOUNT) {
        entity = 'account';
    } else if (entityType === EntityType.CAMPAIGN) {
        entity = 'campaign';
    } else if (entityType === EntityType.AD_GROUP) {
        entity = 'adgroup';
    }

    if (!entity) {
        return null;
    }

    return `/admin/dash/${entity}/${entityId}/change/`;
}

export function doesAnySettingHaveValue(...values: any[]): boolean {
    if (!commonHelpers.isDefined(values) || values.length < 1) {
        return false;
    }
    let settingHasValue = false;
    for (const value of values) {
        if (commonHelpers.isNotEmpty(value)) {
            settingHasValue = true;
            break;
        }
    }
    return settingHasValue;
}
