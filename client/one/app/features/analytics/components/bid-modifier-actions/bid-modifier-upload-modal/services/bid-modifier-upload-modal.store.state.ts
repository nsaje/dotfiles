import {Breakdown} from '../../../../../../app.constants';
import {RequestState} from '../../../../../../shared/types/request-state';
import {BidModifierUploadModalStoreFieldsErrorsState} from './bid-modifier-upload-modal.store.fields-errors';

export class BidModifierUploadModalStoreState {
    adGroupId: number = null;
    breakdown: Breakdown = null;
    file: File = null;
    fieldsErrors = new BidModifierUploadModalStoreFieldsErrorsState();
    requests = {
        import: {} as RequestState,
    };
}
