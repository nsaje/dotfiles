import './bidding-type-setting.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Output,
    Input,
} from '@angular/core';
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
    maxCpc: string;
    @Input()
    maxCpm: string;
    @Input()
    currencySymbol: string;
    @Input()
    biddingTypeErrors: string[];
    @Input()
    maxCpcErrors: string[];
    @Input()
    maxCpmErrors: string[];
    @Output()
    biddingTypeChange = new EventEmitter<BiddingType>();
    @Output()
    maxCpcChange = new EventEmitter<string>();
    @Output()
    maxCpmChange = new EventEmitter<string>();

    BiddingType = BiddingType;

    onBiddingTypeSelect($event: BiddingType) {
        this.biddingTypeChange.emit($event);
    }

    hasCpcBiddingTypeErrors(): boolean {
        return (
            (this.biddingType === BiddingType.CPC &&
                this.biddingTypeErrors &&
                this.biddingTypeErrors.length > 0) ||
            (this.maxCpcErrors && this.maxCpcErrors.length > 0)
        );
    }

    hasCpmBiddingTypeErrors(): boolean {
        return (
            (this.biddingType === BiddingType.CPM &&
                this.biddingTypeErrors &&
                this.biddingTypeErrors.length > 0) ||
            (this.maxCpmErrors && this.maxCpmErrors.length > 0)
        );
    }
}
