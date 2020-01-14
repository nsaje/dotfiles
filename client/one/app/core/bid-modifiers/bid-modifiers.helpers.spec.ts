import {BidModifierType} from '../../app.constants';
import {BidModifierTypeSummary} from './types/bid-modifier-type-summary';
import * as bidModifiersHelpers from './bid-modifiers.helpers';
import {BID_MODIFIER_TYPE_NAME_MAP} from './bid-modifiers.config';

describe('bidModifiersHelpers', () => {
    it('should correctly generate type summary grid row data', () => {
        const bidModifierTypeSummaries: BidModifierTypeSummary[] = [
            {type: BidModifierType.DEVICE, count: 2, min: 0.98, max: 1.05},
        ];
        expect(
            bidModifiersHelpers.convertToTypeSummaryGridRows(
                bidModifierTypeSummaries
            )
        ).toEqual([
            {
                type: BID_MODIFIER_TYPE_NAME_MAP[BidModifierType.DEVICE],
                count: 2,
                limits: {
                    min: 0.98,
                    max: 1.05,
                },
            },
        ]);
    });

    it('should leave unknown bid modifier type string unchanged', () => {
        const bidModifierTypeSummaries: BidModifierTypeSummary[] = [
            {
                type: 'UNKNOWN' as BidModifierType,
                count: 2,
                min: 0.98,
                max: 1.05,
            },
        ];
        expect(
            bidModifiersHelpers.convertToTypeSummaryGridRows(
                bidModifierTypeSummaries
            )
        ).toEqual([
            {
                type: 'UNKNOWN',
                count: 2,
                limits: {
                    min: 0.98,
                    max: 1.05,
                },
            },
        ]);
    });
});
