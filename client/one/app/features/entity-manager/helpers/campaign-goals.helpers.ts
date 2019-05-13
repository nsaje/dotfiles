import * as clone from 'clone';
import {APP_CONSTANTS, CampaignType} from '../../../app.constants';
import {ENTITY_MANAGER_CONFIG} from '../entity-manager.config';

export function extendAvailableGoalsWithEditedGoal(
    editedCampaignGoal: any,
    availableGoals: any[],
    allGoals: any[]
): any[] {
    const newAvailableGoals = clone(availableGoals);
    if (editedCampaignGoal && editedCampaignGoal.type) {
        const item = newAvailableGoals.find((goal: any) => {
            return goal.value === editedCampaignGoal.type;
        });
        if (!item) {
            newAvailableGoals.push(
                allGoals.find((goal: any) => {
                    return goal.value === editedCampaignGoal.type;
                })
            );
        }
    }
    return newAvailableGoals;
}

export function getAvailableGoals(
    allGoals: any[],
    enabledCampaignGoals: any[],
    campaignType: Number,
    onlyCpc: boolean
): any[] {
    return clone(allGoals).filter((goal: any) =>
        isGoalAvailable(goal, enabledCampaignGoals, campaignType, onlyCpc)
    );
}

export function mapAvailableGoalsToCurrencySymbol(
    availableGoals: any[],
    currencySymbol: any
): any[] {
    return availableGoals.map((goal: any) => {
        if (goal.unit === '__CURRENCY__') {
            goal.unit = currencySymbol;
        }
        return goal;
    });
}

function isGoalAvailable(
    option: any,
    enabledCampaignGoals: any[],
    campaignType: Number,
    onlyCpc: boolean
): boolean {
    let isAvailable = true;
    let countConversionGoals = 0;

    if (onlyCpc && option.value !== APP_CONSTANTS.campaignGoalKPI.CPC) {
        return false;
    }

    enabledCampaignGoals.forEach((goal: any) => {
        if (goal.type === option.value) {
            isAvailable = false;
        }
        if (goal.type === APP_CONSTANTS.campaignGoalKPI.CPA) {
            countConversionGoals++;
        }
    });

    if (
        option.value === APP_CONSTANTS.campaignGoalKPI.CPA &&
        countConversionGoals < ENTITY_MANAGER_CONFIG.maxCampaignConversionGoals
    ) {
        return true;
    }

    // Display campaigns do not support CPCV goals
    if (
        campaignType === CampaignType.DISPLAY &&
        option.value === APP_CONSTANTS.campaignGoalKPI.CPCV
    ) {
        return false;
    }

    return isAvailable;
}
