import {Breakdown} from '../../../../../app.constants';
import {RequestState} from '../../../../../shared/types/request-state';
import {BidModifierImportFormStoreFieldsErrorsState} from './bid-modifier-import-form.store.fields-errors';

export class BidModifierImportFormStoreState {
    adGroupId: number = null;
    breakdown: Breakdown = null;
    file: File = null;
    fieldsErrors = new BidModifierImportFormStoreFieldsErrorsState();
    requests = {
        import: {} as RequestState,
    };
}
