import {EntityType} from '../workers.constants';

export interface Hierarchy {
    ids: HierarchyIds;
    children: AccountHierarchyEntity[];
}

export interface HierarchyIds {
    accounts: {
        [key: string]: AccountHierarchyEntity;
    };
    campaigns: {
        [key: string]: CampaignHierarchyEntity;
    };
    adGroups: {
        [key: string]: AdGroupHierarchyEntity;
    };
}

export interface HierarchyEntity<T> {
    id: string;
    name: string;
    parent: HierarchyEntity<T>;
    type: EntityType;
    data: AccountEntity | CampaignEntity | AdGroupEntity;
}

export interface AccountHierarchyEntity extends HierarchyEntity<AccountEntity> {
    children: CampaignHierarchyEntity[];
}

export interface CampaignHierarchyEntity
    extends HierarchyEntity<CampaignEntity> {
    parent: AccountHierarchyEntity;
    children: AdGroupHierarchyEntity[];
}

export interface AdGroupHierarchyEntity extends HierarchyEntity<AdGroupEntity> {
    parent: CampaignHierarchyEntity;
}

export interface AccountEntity {
    id: string;
    name: string;
    campaigns: CampaignEntity[];
}

export interface CampaignEntity {
    id: string;
    name: string;
    adGroups: AdGroupEntity[];
}

export interface AdGroupEntity {
    id: string;
    name: string;
}
