import {CreativeBatch} from '../../../../../core/creatives/types/creative-batch';
import {CreativeBatchStoreFieldsErrorsState} from './creative-batch.store.fields-errors-state';
import {RequestState} from '../../../../../shared/types/request-state';

export class CreativeBatchStoreState {
    entity: CreativeBatch = {
        id: null,
        agencyId: null,
        accountId: null,
        name: null,
        status: null,
        tags: [],
        imageCrop: null,
        displayUrl: null,
        brandName: null,
        description: null,
        callToAction: null,
        createdBy: null,
        createdDt: null,
    };
    fieldsErrors = new CreativeBatchStoreFieldsErrorsState();
    requests = {
        getBatch: {} as RequestState,
        createBatch: {} as RequestState,
        editBatch: {} as RequestState,
        validateBatch: {} as RequestState,
    };
}
