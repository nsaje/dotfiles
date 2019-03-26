import {Breakdown} from '../../../../../../app.constants';
import {FieldsErrors} from '../../../../../../shared/types/fields-errors';
import {BidModifierRequests} from '../../../../../../core/bid-modifiers/types/bid-modifier-requests';

export class BidModifierUploadModalStoreState {
    adGroupId: number = null;
    breakdown: Breakdown = null;
    file: File = null;
    fieldsErrors: FieldsErrors = {};
    requests: BidModifierRequests = {
        import: {},
    };
}
