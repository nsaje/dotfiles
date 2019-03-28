import {Breakdown} from '../../../../../../app.constants';
import {NestedFieldsErrors} from '../../../../../../shared/types/nested-fields-errors';
import {RequestState} from '../../../../../../shared/types/request-state';

export class BidModifierUploadModalStoreState {
    adGroupId: number = null;
    breakdown: Breakdown = null;
    file: File = null;
    fieldsErrors: NestedFieldsErrors = {};
    requests = {
        import: {} as RequestState,
    };
}
