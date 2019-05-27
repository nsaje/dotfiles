import './ad-group-autopilot-state-setting.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Output,
    Input,
    OnChanges,
} from '@angular/core';
import {
    AdGroupAutopilotState,
    CampaignGoalKPI,
} from '../../../../app.constants';
import {AD_GROUP_AUTOPILOT_STATE_SETTING_CONFIG} from './ad-group-autopilot-state-setting.config';

@Component({
    selector: 'zem-ad-group-autopilot-state-setting',
    templateUrl: './ad-group-autopilot-state-setting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdGroupAutopilotStateSettingComponent implements OnChanges {
    @Input()
    autopilotState: AdGroupAutopilotState;
    @Input()
    optimizationObjective: CampaignGoalKPI;
    @Input()
    isDisabled: boolean;
    @Output()
    autopilotStateChange = new EventEmitter<AdGroupAutopilotState>();

    AdGroupAutopilotState = AdGroupAutopilotState;
    optimizationObjectiveText: string;
    cpaOptimizationNote: string;

    ngOnChanges() {
        this.optimizationObjectiveText = this.getOptimizationObjectiveText(
            this.optimizationObjective
        );
        this.cpaOptimizationNote = this.getCpaOptimizationNote(
            this.optimizationObjective
        );
    }

    private getOptimizationObjectiveText(
        optimizationObjective: CampaignGoalKPI
    ): string {
        return (
            AD_GROUP_AUTOPILOT_STATE_SETTING_CONFIG.optimizationObjectivesTexts[
                optimizationObjective
            ] ||
            AD_GROUP_AUTOPILOT_STATE_SETTING_CONFIG.optimizationObjectivesTexts
                .default
        );
    }

    private getCpaOptimizationNote(
        optimizationObjective: CampaignGoalKPI
    ): string {
        if (optimizationObjective !== CampaignGoalKPI.CPA) {
            return null;
        }
        return (
            'Note: CPA optimization works best when at least ' +
            '20 conversions have occurred in the past two weeks.'
        );
    }
}
