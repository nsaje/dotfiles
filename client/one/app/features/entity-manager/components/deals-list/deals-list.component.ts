import './deals-list.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    TemplateRef,
    ContentChild,
} from '@angular/core';
import {Deal} from '../../../../core/deals/types/deal';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';

@Component({
    selector: 'zem-deals-list',
    templateUrl: './deals-list.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DealsListComponent {
    @Input()
    deals: Deal[];
    @Input()
    availableDeals: Deal[];
    @Input()
    isLoading: boolean = false;
    @Input()
    isDisabled: boolean;
    @Output()
    dealSelect = new EventEmitter<Deal>();
    @Output()
    search = new EventEmitter<string>();
    @Output()
    open = new EventEmitter<void>();

    @ContentChild('dealItemTemplate', {read: TemplateRef, static: false})
    dealItemTemplate: TemplateRef<any>;

    onDealSelect(deal: Deal) {
        this.dealSelect.emit(deal);
    }

    onSearch($event: string) {
        this.search.emit($event);
    }

    selectSearchFn(term: string, deal: Deal) {
        term = term.toLowerCase();
        return (
            commonHelpers
                .getValueOrDefault(deal.name, '')
                .toLowerCase()
                .indexOf(term) > -1 ||
            commonHelpers
                .getValueOrDefault(deal.source, '')
                .toLowerCase()
                .indexOf(term) > -1 ||
            commonHelpers
                .getValueOrDefault(deal.dealId, '')
                .toLowerCase()
                .indexOf(term) > -1
        );
    }
}
