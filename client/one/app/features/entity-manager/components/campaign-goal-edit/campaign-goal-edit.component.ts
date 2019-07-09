import './campaign-goal-edit.component.less';

import {
    Component,
    OnChanges,
    SimpleChanges,
    Input,
    Output,
    EventEmitter,
    ChangeDetectionStrategy,
} from '@angular/core';
import {CampaignGoal} from '../../../../core/entities/types/campaign/campaign-goal';
import {
    CAMPAIGN_CONVERSION_GOAL_TYPES,
    CONVERSION_WINDOWS,
    CAMPAIGN_GOAL_KPIS,
} from '../../entity-manager.config';
import {
    CampaignGoalKPI,
    CampaignConversionGoalType,
    ConversionWindow,
    Currency,
} from '../../../../app.constants';
import {CampaignConversionGoal} from 'one/app/core/entities/types/campaign/campaign-conversion-goal';
import {ConversionPixel} from '../../../../core/conversion-pixels/types/conversion-pixel';
import * as currencyHelpers from '../../../../shared/helpers/currency.helpers';
import * as campaignGoalsHelpers from '../../helpers/campaign-goals.helpers';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {CampaignGoalKPIConfig} from '../../types/campaign-goal-kpi-config';
import {ConversionWindowConfig} from '../../../../core/conversion-pixels/types/conversion-windows-config';
import {CampaignGoalError} from '../../types/campaign-goal-error';
import {DataType, Unit} from '../../../../app.constants';
import * as unitsHelpers from '../../../../shared/helpers/units.helpers';

@Component({
    selector: 'zem-campaign-goal-edit',
    templateUrl: './campaign-goal-edit.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CampaignGoalEditComponent implements OnChanges {
    @Input()
    campaignGoal: CampaignGoal;
    @Input()
    currency: Currency;
    @Input()
    availableCampaignGoals: CampaignGoalKPIConfig[];
    @Input()
    conversionPixels: ConversionPixel[];
    @Input()
    availableConversionPixels: ConversionPixel[];
    @Input()
    campaignGoalError: CampaignGoalError;
    @Output()
    campaignGoalChange = new EventEmitter<ChangeEvent<CampaignGoal>>();

    availableGoals: CampaignGoalKPIConfig[] = [];
    availablePixels: ConversionPixel[] = [];
    availableWindows: ConversionWindowConfig[] = [];
    editedGoalConfig: CampaignGoalKPIConfig;

    // options
    CAMPAIGN_CONVERSION_GOAL_TYPES = CAMPAIGN_CONVERSION_GOAL_TYPES;

    // enums
    DataType = DataType;
    CampaignConversionGoalType = CampaignConversionGoalType;

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.availableCampaignGoals) {
            this.availableGoals = campaignGoalsHelpers.extendAvailableGoalsWithEditedGoal(
                this.campaignGoal,
                this.availableCampaignGoals,
                CAMPAIGN_GOAL_KPIS
            );
        }
        if (changes.availableConversionPixels) {
            this.availablePixels = campaignGoalsHelpers.extendAvailableConversionPixelsWithEditedConversionPixel(
                this.campaignGoal.conversionGoal
                    ? this.campaignGoal.conversionGoal.goalId
                    : null,
                this.availableConversionPixels,
                this.conversionPixels
            );
            this.availableWindows = this.getAvailableWindows(
                this.campaignGoal,
                this.availablePixels
            );
        }
        if (changes.campaignGoal) {
            this.editedGoalConfig = campaignGoalsHelpers.findCampaignGoalConfig(
                this.campaignGoal,
                this.availableGoals
            );
        }
    }

    onGoalValueChange($event: string) {
        this.campaignGoalChange.emit({
            target: this.campaignGoal,
            changes: {
                value: $event,
            },
        });
    }

    onGoalTypeChange($event: CampaignGoalKPI) {
        this.campaignGoalChange.emit({
            target: this.campaignGoal,
            changes: {
                type: $event,
            },
        });
    }

    onConversionGoalTypeChange($event: CampaignConversionGoalType) {
        const conversionGoal: CampaignConversionGoal = {
            type: $event,
            conversionWindow: null,
            goalId: null,
            pixelUrl: null,
            name: null,
        };
        this.campaignGoalChange.emit({
            target: this.campaignGoal,
            changes: {
                conversionGoal: conversionGoal,
            },
        });
    }

    onConversionGoalIdChange($event: string) {
        this.campaignGoalChange.emit({
            target: this.campaignGoal,
            changes: {
                conversionGoal: {
                    ...this.campaignGoal.conversionGoal,
                    goalId: $event,
                },
            },
        });
    }

    onConversionGoalWindowChange($event: ConversionWindow) {
        this.campaignGoalChange.emit({
            target: this.campaignGoal,
            changes: {
                conversionGoal: {
                    ...this.campaignGoal.conversionGoal,
                    conversionWindow: $event,
                },
            },
        });
    }

    getGoalUnitText(): string {
        return unitsHelpers.getUnitText(
            this.editedGoalConfig.unit,
            this.currency
        );
    }

    private getAvailableWindows(
        campaignGoal: CampaignGoal,
        availablePixels: ConversionPixel[]
    ): ConversionWindowConfig[] {
        let availableWindows: ConversionWindowConfig[] = [];
        if (
            campaignGoal.conversionGoal &&
            campaignGoal.conversionGoal.type ===
                CampaignConversionGoalType.PIXEL
        ) {
            const conversionPixel = availablePixels.find(conversionPixel => {
                return (
                    conversionPixel.id === campaignGoal.conversionGoal.goalId
                );
            });
            if (conversionPixel) {
                availableWindows = campaignGoalsHelpers.extendAvailableConversionWindowsWithEditedConversionWindow(
                    campaignGoal.conversionGoal.conversionWindow,
                    conversionPixel.conversionWindows,
                    CONVERSION_WINDOWS
                );
            }
        }
        return availableWindows;
    }
}
