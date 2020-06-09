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
        return 'This ad group will be automatically paused to allow you to review the bids and daily spend caps of all RTB sources. Please check the bids and daily spend caps on the media sources tab before you enable the ad group.';
    }
}

export function getAutopilotChangeConfirmMessage(
    autopilotState: boolean
): string {
    if (autopilotState) {
        return (
            "Once campaign budget optimization is enabled, ad groups' " +
            "flight time settings will be reset and won't be respected " +
            'anymore. Budget flight time will be used for running ' +
            "campaign's ad groups. Additionally, daily spend caps and " +
            'bids settings will be disabled.\n\nAre you sure you want to ' +
            'enable campaign budget optimization?'
        );
    }
    return (
        'You are about to disable campaign budget optimization. ' +
        "Please check ad groups' flight times, daily spend caps and " +
        'bids settings after settings are saved.\n\nAre you ' +
        'sure you want to disable campaign budget optimization?'
    );
}
