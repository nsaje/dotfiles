import './bidding-strategy-setting.component.less';

import {
    ChangeDetectionStrategy,
    Component,
    EventEmitter,
    Input,
    OnChanges,
    Output,
    SimpleChanges,
} from '@angular/core';
import {AdGroupAutopilotState, BiddingType} from '../../../../app.constants';

@Component({
    selector: 'zem-bidding-strategy-setting',
    templateUrl: './bidding-strategy-setting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BiddingStrategySettingComponent implements OnChanges {
    @Input()
    biddingType: BiddingType;
    @Input()
    autopilotState: AdGroupAutopilotState;
    @Input()
    isDisabled: boolean;
    @Output()
    autopilotStateChange = new EventEmitter<AdGroupAutopilotState>();

    formattedAutopilotState: AdGroupAutopilotState;

    AdGroupAutopilotState = AdGroupAutopilotState;

    // We want to display ad groups with autopilot state set to the legacy options of ACTIVE_CPC_BUDGET and ACTIVE_CPC as ACTIVE
    ngOnChanges(changes: SimpleChanges): void {
        if (changes.autopilotState) {
            this.formattedAutopilotState =
                this.autopilotState === AdGroupAutopilotState.INACTIVE
                    ? AdGroupAutopilotState.INACTIVE
                    : AdGroupAutopilotState.ACTIVE;
        }
    }
}
