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
    @Output()
    dealRemove = new EventEmitter<Deal>();

    isEditFormVisible: boolean = false;

    ngOnInit(): void {
        this.isEditFormVisible = !this.deal.id;
    }

    removeDeal() {
        this.dealRemove.emit(this.deal);
    }

    formatDate(date: Date): string {
        return commonHelpers.isDefined(date)
            ? moment(date).format('MM/DD/YYYY')
            : 'N/A';
    }
}
