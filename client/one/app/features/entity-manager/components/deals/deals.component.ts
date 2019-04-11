import './deals.component.less';

import {Component, ChangeDetectionStrategy, Input} from '@angular/core';
import {Deal} from '../../../../core/entities/types/common/deal';

@Component({
    selector: 'zem-deals',
    templateUrl: './deals.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DealsComponent {
    @Input()
    deals: Deal[];

    showOnlyApplied: boolean = true;
}
