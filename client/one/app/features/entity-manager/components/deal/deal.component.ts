import './deal.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    OnInit,
} from '@angular/core';
import {Deal} from '../../../../core/deals/types/deal';
import * as moment from 'moment';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';

@Component({
    selector: 'zem-deal',
    templateUrl: './deal.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DealComponent implements OnInit {
    @Input()
    deal: Deal;
    @Input()
    isDisabled: boolean;
    @Output()
    dealRemove = new EventEmitter<Deal>();
    @Output()
    dealEditFormClose = new EventEmitter<void>();

    isEditFormVisible: boolean = false;

    ngOnInit(): void {
        this.isEditFormVisible = !this.deal.id;
    }

    removeDeal() {
        this.dealRemove.emit(this.deal);
    }

    toggleDealEditForm() {
        this.isEditFormVisible = !this.isEditFormVisible;
        if (!this.isEditFormVisible) {
            this.dealEditFormClose.emit();
        }
    }

    formatDate(date: Date): string {
        return commonHelpers.isDefined(date)
            ? moment(date).format('MM/DD/YYYY')
            : 'N/A';
    }
}
