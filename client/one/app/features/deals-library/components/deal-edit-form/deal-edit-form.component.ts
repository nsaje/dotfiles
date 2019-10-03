import './deal-edit-form.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {Deal} from '../../../../core/deals/types/deal';

@Component({
    selector: 'zem-deal-edit-form',
    templateUrl: './deal-edit-form.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DealEditFormComponent {
    @Input()
    deal: Deal;
    @Input()
    dealErrors: any;
    @Input()
    sourceOptions: any[];
    @Output()
    dealChange = new EventEmitter<ChangeEvent<Deal>>();

    onNameChange(name: string) {
        this.dealChange.emit({
            target: this.deal,
            changes: {
                name: name,
            },
        });
    }

    onDealIdChange(dealId: string) {
        this.dealChange.emit({
            target: this.deal,
            changes: {
                dealId: dealId,
            },
        });
    }

    onSourceChange(source: string) {
        this.dealChange.emit({
            target: this.deal,
            changes: {
                source: source,
            },
        });
    }

    onFloorPriceChange(floorPrice: string) {
        this.dealChange.emit({
            target: this.deal,
            changes: {
                floorPrice: floorPrice,
            },
        });
    }

    onValidFromDateChange(validFromDate: Date) {
        this.dealChange.emit({
            target: this.deal,
            changes: {
                validFromDate: validFromDate,
            },
        });
    }

    onValidToDateChange(validToDate: Date) {
        this.dealChange.emit({
            target: this.deal,
            changes: {
                validToDate: validToDate,
            },
        });
    }

    onDescriptionChange(description: string) {
        this.dealChange.emit({
            target: this.deal,
            changes: {
                description: description,
            },
        });
    }
}
