import * as clone from 'clone';
import {
    CampaignGoalKPI,
    CampaignType,
    Currency,
    ConversionWindow,
    Unit,
    DataType,
    APP_CONSTANTS,
} from '../../../app.constants';
import {
    ENTITY_MANAGER_CONFIG,
    CAMPAIGN_GOAL_VALUE_TEXT,
    CAMPAIGN_GOAL_KPIS,
} from '../entity-manager.config';
import {ConversionPixel} from '../../../core/conversion-pixels/types/conversion-pixel';
import {CampaignGoal} from '../../../core/entities/types/campaign/campaign-goal';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import * as numericHelpers from '../../../shared/helpers/numeric.helpers';
import * as currencyHelpers from '../../../shared/helpers/currency.helpers';
import {CampaignGoalKPIConfig} from '../types/campaign-goal-kpi-config';
import {ConversionWindowConfig} from '../../../core/conversion-pixels/types/conversion-windows-config';
import {CONVERSION_PIXEL_CLICK_WINDOWS} from '../../../core/conversion-pixels/conversion-pixels.config';

export function findCampaignGoalConfig(
    campaignGoal: CampaignGoal,
    availableConfigs: CampaignGoalKPIConfig[]
): CampaignGoalKPIConfig {
    return (
        availableConfigs.find(goalConfig => {
            return goalConfig.value === campaignGoal.type;
        }) || {name: null, value: null, dataType: null}
    );
}

export function extendAvailableGoalsWithEditedGoal(
    editedCampaignGoal: CampaignGoal,
    availableGoals: CampaignGoalKPIConfig[],
    allGoals: CampaignGoalKPIConfig[]
): CampaignGoalKPIConfig[] {
    const newAvailableGoals = clone(availableGoals) || [];
    if (editedCampaignGoal && editedCampaignGoal.type) {
        let item = newAvailableGoals.find(goal => {
            return goal.value === editedCampaignGoal.type;
        });
        if (!item && allGoals.length > 0) {
            item = allGoals.find(goal => {
                return goal.value === editedCampaignGoal.type;
            });
            if (item) {
                newAvailableGoals.push(item);
            }
        }
    }
    return newAvailableGoals;
}

export function getAvailableGoals(
    allGoals: CampaignGoalKPIConfig[],
    enabledCampaignGoals: CampaignGoal[],
    campaignType: CampaignType
): CampaignGoalKPIConfig[] {
    return clone(allGoals).filter(goal =>
        isGoalAvailable(goal, enabledCampaignGoals, campaignType)
    );
}

function isGoalAvailable(
    option: CampaignGoalKPIConfig,
    enabledCampaignGoals: CampaignGoal[],
    campaignType: CampaignType
): boolean {
    // TODO (msuber): simplify when legacy ajs components will no longer
    // use this helper function

    let isAvailable = true;
    let countConversionGoals = 0;

    enabledCampaignGoals.forEach(goal => {
        if (goal.type === option.value) {
            isAvailable = false;
        }

        if (
            commonHelpers.isEqualToAnyItem(goal.type, [
                CampaignGoalKPI.CPA,
                APP_CONSTANTS.campaignGoalKPI.CPA,
            ])
        ) {
            countConversionGoals++;
        }
    });

    if (
        commonHelpers.isEqualToAnyItem(option.value, [
            CampaignGoalKPI.CPA,
            APP_CONSTANTS.campaignGoalKPI.CPA,
        ]) &&
        countConversionGoals < ENTITY_MANAGER_CONFIG.maxCampaignConversionGoals
    ) {
        return true;
    }

    // Display campaigns do not support CPCV goals
    if (
        commonHelpers.isEqualToAnyItem(campaignType, [
            CampaignType.DISPLAY,
            APP_CONSTANTS.campaignTypes.DISPLAY,
        ]) &&
        commonHelpers.isEqualToAnyItem(option.value, [
            CampaignGoalKPI.CPCV,
            APP_CONSTANTS.campaignGoalKPI.CPCV,
        ])
    ) {
        return false;
    }

    return isAvailable;
}

export function getConversionPixelsWithAvailableConversionWindows(
    campaignGoals: CampaignGoal[],
    conversionPixels: ConversionPixel[]
): ConversionPixel[] {
    const newConversionPixels: ConversionPixel[] = [];
    clone(conversionPixels).forEach(conversionPixel => {
        if (conversionPixel.archived) {
            return;
        }
        conversionPixel.conversionWindows = [];
        const counts = {};
        campaignGoals.forEach(campaignGoal => {
            if (campaignGoal.type !== CampaignGoalKPI.CPA) {
                return;
            }
            if (
                campaignGoal.conversionGoal.goalId === conversionPixel.id &&
                !counts[campaignGoal.conversionGoal.conversionWindow]
            ) {
                counts[campaignGoal.conversionGoal.conversionWindow] =
                    campaignGoal.conversionGoal.conversionWindow;
            }
        });
        CONVERSION_PIXEL_CLICK_WINDOWS.forEach(conversionWindow => {
            if (!counts[conversionWindow.value]) {
                conversionPixel.conversionWindows.push(conversionWindow);
            }
        });
        if (conversionPixel.conversionWindows.length > 0) {
            newConversionPixels.push(conversionPixel);
        }
    });
    return newConversionPixels;
}

export function extendAvailableConversionPixelsWithEditedConversionPixel(
    goalId: string,
    availableConversionPixels: ConversionPixel[],
    allConversionPixels: ConversionPixel[]
): ConversionPixel[] {
    const newAvailableConversionPixels = clone(availableConversionPixels) || [];
    if (goalId) {
        let item = newAvailableConversionPixels.find(conversionPixel => {
            return conversionPixel.id === goalId;
        });
        if (!item && allConversionPixels.length > 0) {
            item = allConversionPixels.find(conversionPixel => {
                return conversionPixel.id === goalId;
            });
            if (item) {
                newAvailableConversionPixels.push(item);
            }
        }
    }
    return newAvailableConversionPixels;
}

export function extendAvailableConversionWindowsWithEditedConversionWindow(
    editedConversionWindow: ConversionWindow,
    availableConversionWindows: ConversionWindowConfig[],
    allConversionWindows: ConversionWindowConfig[]
): ConversionWindowConfig[] {
    const newAvailableConversionWindows =
        clone(availableConversionWindows) || [];
    if (editedConversionWindow) {
        let item = newAvailableConversionWindows.find(conversionWindow => {
            return conversionWindow.value === editedConversionWindow;
        });
        if (!item && allConversionWindows.length > 0) {
            item = allConversionWindows.find(conversionWindow => {
                return conversionWindow.value === editedConversionWindow;
            });
            if (item) {
                newAvailableConversionWindows.push(item);
            }
        }
    }
    return newAvailableConversionWindows;
}

export function getCampaignGoalDescription(
    campaignGoal: CampaignGoal,
    currency: Currency
): string {
    if (!commonHelpers.isDefined(campaignGoal)) {
        return '';
    }

    const campaignGoalConfig = findCampaignGoalConfig(
        campaignGoal,
        CAMPAIGN_GOAL_KPIS
    );

    if (campaignGoalConfig.dataType === DataType.Currency) {
        return getDescriptionForCurrencyGoalValue(campaignGoal, currency);
    } else if (campaignGoalConfig.dataType === DataType.Decimal) {
        return getDescriptionForDecimalGoalValue(
            campaignGoal,
            campaignGoalConfig.unit
        );
    } else {
        return '';
    }
}

function getDescriptionForCurrencyGoalValue(
    campaignGoal: CampaignGoal,
    currency: Currency
): string {
    let fractionSize = 2;
    if (campaignGoal.type === CampaignGoalKPI.CPC) {
        fractionSize = 3;
    }
    const formattedValue = currencyHelpers.getValueInCurrency(
        campaignGoal.value,
        currency,
        fractionSize
    );
    return `${formattedValue} ${CAMPAIGN_GOAL_VALUE_TEXT[campaignGoal.type]}`;
}

function getDescriptionForDecimalGoalValue(
    campaignGoal: CampaignGoal,
    unit: Unit
): string {
    const formattedValue = numericHelpers.parseDecimal(campaignGoal.value, 2);
    const unitWhitespace = unit === Unit.Percent ? '' : ' '; // Omit whitespace before percentage unit sign
    return `${formattedValue}${unitWhitespace}${
        CAMPAIGN_GOAL_VALUE_TEXT[campaignGoal.type]
    }`;
}
