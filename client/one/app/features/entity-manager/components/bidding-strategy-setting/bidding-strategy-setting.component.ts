import './bidding-strategy-setting.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Output,
    Input,
} from '@angular/core';
import {AdGroupAutopilotState, BiddingType} from '../../../../app.constants';

@Component({
    selector: 'zem-bidding-strategy-setting',
    templateUrl: './bidding-strategy-setting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BiddingStrategySettingComponent {
    @Input()
    biddingType: BiddingType;
    @Input()
    autopilotState: AdGroupAutopilotState;
    @Input()
    isDisabled: boolean;
    @Output()
    autopilotStateChange = new EventEmitter<AdGroupAutopilotState>();

    AdGroupAutopilotState = AdGroupAutopilotState;
}
