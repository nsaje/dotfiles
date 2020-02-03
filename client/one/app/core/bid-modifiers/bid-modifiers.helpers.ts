import {BID_MODIFIER_TYPE_NAME_MAP} from './bid-modifiers.config';
import {BidModifierTypeSummary} from './types/bid-modifier-type-summary';
import {TypeSummaryGridRow} from '../../shared/components/bid-modifier-types-grid/services/type-summary-grid-row';
import * as commonHelpers from '../../shared/helpers/common.helpers';

export function convertToTypeSummaryGridRows(
    typeSummaries: BidModifierTypeSummary[]
): TypeSummaryGridRow[] {
    if (!commonHelpers.isDefined(typeSummaries)) {
        return null;
    }

    return typeSummaries.map(item => {
        return {
            type: BID_MODIFIER_TYPE_NAME_MAP[item.type]
                ? BID_MODIFIER_TYPE_NAME_MAP[item.type]
                : item.type,
            count: item.count,
            limits: {
                min: item.min,
                max: item.max,
            },
        };
    });
}
