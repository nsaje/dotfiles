import {AdGroupState, EntityType} from '../../../app.constants';

export function getClosingUnsavedChangesConfirmMessage(): string {
    return 'You have unsaved changes.\nAre you sure you want to close settings?';
}

export function getManageRtbSourcesAsOneChangeConfirmMessage(
    adGroupState: AdGroupState,
    manageRtbSourcesAsOne: boolean
): string {
    if (manageRtbSourcesAsOne && adGroupState === AdGroupState.INACTIVE) {
        return 'One joint Bid and Daily Spend Cap will be set for all RTB sources. Please check the Daily Spend Cap in the Media Sources tab before enabling the ad group.';
    } else if (manageRtbSourcesAsOne && adGroupState === AdGroupState.ACTIVE) {
        return 'This ad group will be automatically paused to set one joint Bid and Daily Spend Cap for all RTB sources. Please check the Daily Spend Cap in the Media Sources tab before enabling the ad group.';
    } else if (
        !manageRtbSourcesAsOne &&
        adGroupState === AdGroupState.INACTIVE
    ) {
        return 'Bids and Daily Spend Caps of all RTB sources will be reset. Please check Daily Spend Caps in the Media Sources tab before you enable the ad group.';
    } else if (!manageRtbSourcesAsOne && adGroupState === AdGroupState.ACTIVE) {
        return 'This ad group will be automatically paused to reset the Bids and Daily Spend Caps of all RTB sources. Please check Daily Spend Caps in the Media Sources tab before you enable the ad group.';
    }
}

export function getDisabledArchiveActionText(entityType: EntityType) {
    if (entityType === EntityType.ACCOUNT) {
        return "All of the account's campaigns have to be paused in order to archive the account.";
    }
    if (entityType === EntityType.CAMPAIGN) {
        return "All of the campaign's ad groups have to be paused in order to archive the campaign.";
    }
    if (entityType === EntityType.AD_GROUP) {
        return 'An ad group has to be paused for 3 days in order to archive it.';
    }
    return null;
}
