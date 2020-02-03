import {Injectable} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {BidModifiersOverviewStoreState} from './bid-modifiers-overview.store.state';
import {BidModifierTypeSummary} from '../../../../core/bid-modifiers/types/bid-modifier-type-summary';
import {convertToTypeSummaryGridRows} from '../../../../core/bid-modifiers/bid-modifiers.helpers';

@Injectable()
export class BidModifiersOverviewStore extends Store<
    BidModifiersOverviewStoreState
> {
    constructor() {
        super(new BidModifiersOverviewStoreState());
    }

    updateTypeSummaryGridRows(
        bidModifierTypeSummaries: BidModifierTypeSummary[]
    ): void {
        const typeSummaryGridRows = convertToTypeSummaryGridRows(
            bidModifierTypeSummaries
        );

        this.setState({
            ...this.state,
            typeSummaryGridRows: typeSummaryGridRows,
        });
    }
}
