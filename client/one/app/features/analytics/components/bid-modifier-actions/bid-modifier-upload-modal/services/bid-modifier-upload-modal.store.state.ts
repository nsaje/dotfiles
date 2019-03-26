import {Breakdown} from '../../../../../../app.constants';
import {NestedFieldsErrors} from '../../../../../../shared/types/nested-fields-errors';
import {BidModifierRequests} from '../../../../../../core/bid-modifiers/types/bid-modifier-requests';

export class BidModifierUploadModalStoreState {
    adGroupId: number = null;
    breakdown: Breakdown = null;
    file: File = null;
    fieldsErrors: NestedFieldsErrors = {};
    requests: BidModifierRequests = {
        import: {},
    };
}
