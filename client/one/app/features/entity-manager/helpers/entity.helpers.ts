import {EntityType} from '../../../app.constants';

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
