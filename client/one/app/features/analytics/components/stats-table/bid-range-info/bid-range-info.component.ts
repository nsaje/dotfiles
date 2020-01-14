import './bid-range-info.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnChanges,
    Input,
} from '@angular/core';
import {BidRangeInfoStore} from './services/bid-range-info.store';
import {BidModifier} from '../../../../../core/bid-modifiers/types/bid-modifier';
import {
    Currency,
    BiddingType,
    AdGroupAutopilotState,
} from '../../../../../app.constants';
import {BidModifierTypeSummary} from '../../../../../core/bid-modifiers/types/bid-modifier-type-summary';

@Component({
    selector: 'zem-bid-range-info',
    templateUrl: './bid-range-info.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [BidRangeInfoStore],
})
export class BidRangeInfoComponent implements OnChanges {
    @Input()
    bidModifier: BidModifier;
    @Input()
    biddingType: BiddingType;
    @Input()
    bid: string;
    @Input()
    bidModifierTypeSummaries: BidModifierTypeSummary[];
    @Input()
    currency: Currency;
    @Input()
    fractionSize: number;
    @Input()
    adGroupAutopilotState: AdGroupAutopilotState;
    @Input()
    modifierPercent: string = null;

    constructor(public store: BidRangeInfoStore) {}

    ngOnChanges(): void {
        this.store.updateInputs(
            this.bidModifier,
            this.biddingType,
            this.bid,
            this.bidModifierTypeSummaries,
            this.currency,
            this.fractionSize,
            this.adGroupAutopilotState,
            this.modifierPercent
        );
    }
}
