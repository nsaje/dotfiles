import './bidding-type-setting.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Output,
    Input,
} from '@angular/core';
import {AdGroupAutopilotState} from '../../../../app.constants';
import {BiddingType} from '../../../../app.constants';

@Component({
    selector: 'zem-bidding-type-setting',
    templateUrl: './bidding-type-setting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BiddingTypeSettingComponent {
    @Input()
    biddingType: BiddingType;
    @Input()
    bid: string;
    @Input()
    maxBid: string;
    @Input()
    currencySymbol: string;
    @Input()
    autopilotState: AdGroupAutopilotState;
    @Input()
    biddingTypeErrors: string[];
    @Input()
    bidErrors: string[];
    @Input()
    maxBidErrors: string[];
    @Output()
    biddingTypeChange = new EventEmitter<BiddingType>();
    @Output()
    bidChange = new EventEmitter<string>();
    @Output()
    maxBidChange = new EventEmitter<string>();

    BiddingType = BiddingType;

    onBiddingTypeSelect($event: BiddingType) {
        this.biddingTypeChange.emit($event);
    }

    hasBidErrors(): boolean {
        return (
            (this.biddingTypeErrors && this.biddingTypeErrors.length > 0) ||
            (this.bidErrors && this.bidErrors.length > 0) ||
            (this.maxBidErrors && this.maxBidErrors.length > 0)
        );
    }

    isAutopilotActive(): boolean {
        return this.autopilotState !== AdGroupAutopilotState.INACTIVE;
    }
}
