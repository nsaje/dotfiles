import './campaign-goals.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    OnChanges,
    SimpleChanges,
    Output,
    EventEmitter,
} from '@angular/core';
import {CampaignGoal} from '../../../../core/entities/types/campaign/campaign-goal';
import {
    AUTOMATICALLY_OPTIMIZED_KPI_GOALS,
    CAMPAIGN_GOAL_VALUE_TEXT,
    CAMPAIGN_GOAL_KPIS,
} from '../../entity-manager.config';
import * as commonHelper from '../../../../shared/helpers/common.helpers';
import * as campaignGoalsHelpers from '../../helpers/campaign-goals.helpers';
import {CampaignType, Currency} from '../../../../app.constants';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {ConversionPixel} from '../../../../core/conversion-pixels/types/conversion-pixel';
import {CampaignGoalKPIConfig} from '../../types/campaign-goal-kpi-config';
import {CampaignGoalError} from '../../types/campaign-goal-error';

@Component({
    selector: 'zem-campaign-goals',
    templateUrl: './campaign-goals.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CampaignGoalsComponent implements OnChanges {
    @Input()
    campaignType: CampaignType;
    @Input()
    onlyCpc: boolean;
    @Input()
    currency: Currency;
    @Input()
    campaignGoals: CampaignGoal[];
    @Input()
    conversionPixels: ConversionPixel[];
    @Input()
    campaignGoalsErrors: CampaignGoalError[];
    @Output()
    campaignGoalCreate = new EventEmitter<void>();
    @Output()
    campaignGoalPrimaryChange = new EventEmitter<CampaignGoal>();
    @Output()
    campaignGoalChange = new EventEmitter<ChangeEvent<CampaignGoal>>();
    @Output()
    campaignGoalDelete = new EventEmitter<CampaignGoal>();

    availableCampaignGoals: CampaignGoalKPIConfig[] = [];
    availableConversionPixels: ConversionPixel[] = [];

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.conversionPixels) {
            this.availableConversionPixels = campaignGoalsHelpers.getConversionPixelsWithAvailableConversionWindows(
                this.campaignGoals,
                this.conversionPixels
            );
        }
        if (changes.campaignGoals) {
            this.availableCampaignGoals = campaignGoalsHelpers.getAvailableGoals(
                CAMPAIGN_GOAL_KPIS,
                this.campaignGoals,
                this.campaignType,
                this.onlyCpc
            );
            this.availableConversionPixels = campaignGoalsHelpers.getConversionPixelsWithAvailableConversionWindows(
                this.campaignGoals,
                this.conversionPixels
            );
        }
    }

    trackByIndex(index: number): string {
        return index.toString();
    }

    getKPIOptimizationLabel(): string {
        const campaignGoal = (this.campaignGoals || []).find(campaignGoal => {
            return (
                campaignGoal.primary &&
                AUTOMATICALLY_OPTIMIZED_KPI_GOALS.indexOf(campaignGoal.type) >
                    -1
            );
        });
        if (commonHelper.isDefined(campaignGoal)) {
            return `Goal ${
                CAMPAIGN_GOAL_VALUE_TEXT[campaignGoal.type]
            } is automatically optimized when data from Google Analytics/Adobe Analytics is available and there are enough clicks for the data to be statistically significant.`;
        }
        return null;
    }

    onCampaignGoalPrimaryChange(campaignGoal: CampaignGoal) {
        this.campaignGoalPrimaryChange.emit(campaignGoal);
    }

    onCampaignGoalChange($event: ChangeEvent<CampaignGoal>) {
        this.campaignGoalChange.emit($event);
    }

    onCampaignGoalDelete($event: CampaignGoal) {
        this.campaignGoalDelete.emit($event);
    }

    createGoal(): void {
        this.campaignGoalCreate.emit();
    }

    hasError(index: number): boolean {
        if (this.campaignGoalsErrors.length > 0) {
            const campaignGoalErrors = (this.campaignGoalsErrors || [])[index];
            if (
                commonHelper.isDefined(campaignGoalErrors) &&
                Object.keys(campaignGoalErrors).length > 0
            ) {
                return true;
            }
        }
        return false;
    }
}
