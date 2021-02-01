import {
    AccountEntity,
    Hierarchy,
    CampaignEntity,
    AdGroupEntity,
    AccountHierarchyEntity,
    CampaignHierarchyEntity,
    AdGroupHierarchyEntity,
} from '../types/hierarchy';
import {EntityType} from '../workers.constants';

export function buildHierarchy(entities: AccountEntity[]): Hierarchy {
    const hierarchy: Hierarchy = {
        ids: {
            accounts: {},
            campaigns: {},
            adGroups: {},
        },
        children: [] as AccountHierarchyEntity[],
    };

    hierarchy.children = entities.map((entity: AccountEntity) => {
        const account: AccountHierarchyEntity = createHierarchyEntity(
            EntityType.ACCOUNT,
            null,
            entity
        ) as AccountHierarchyEntity;
        hierarchy.ids.accounts[account.id] = account;
        account.children = entity.campaigns.map((entity: CampaignEntity) => {
            const campaign: CampaignHierarchyEntity = createHierarchyEntity(
                EntityType.CAMPAIGN,
                account,
                entity
            ) as CampaignHierarchyEntity;
            hierarchy.ids.campaigns[campaign.id] = campaign;
            campaign.children = entity.adGroups.map((entity: AdGroupEntity) => {
                const adGroup: AdGroupHierarchyEntity = createHierarchyEntity(
                    EntityType.AD_GROUP,
                    campaign,
                    entity
                ) as AdGroupHierarchyEntity;
                hierarchy.ids.adGroups[adGroup.id] = adGroup;
                return adGroup;
            });
            return campaign;
        });
        return account;
    });

    return hierarchy;
}

function createHierarchyEntity(
    type: EntityType,
    parent: AccountHierarchyEntity | CampaignHierarchyEntity,
    data: AccountEntity | CampaignEntity | AdGroupEntity
): AccountHierarchyEntity | CampaignHierarchyEntity | AdGroupHierarchyEntity {
    return {
        id: data.id,
        name: data.name,
        parent: parent,
        type: type,
        data: data,
        children: [],
    };
}
