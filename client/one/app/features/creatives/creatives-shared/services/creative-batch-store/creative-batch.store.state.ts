import {CreativeBatch} from '../../../../../core/creatives/types/creative-batch';
import {CreativeBatchStoreFieldsErrorsState} from './creative-batch.store.fields-errors-state';
import {RequestState} from '../../../../../shared/types/request-state';
import {CreativeCandidate} from '../../../../../core/creatives/types/creative-candidate';

export class CreativeBatchStoreState {
    entity: CreativeBatch = {
        id: null,
        agencyId: null,
        accountId: null,
        type: null,
        mode: null,
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
    candidates: CreativeCandidate[] = [];
    selectedCandidateId: string | undefined = undefined;
    fieldsErrors = new CreativeBatchStoreFieldsErrorsState();
    requests = {
        getBatch: {} as RequestState,
        createBatch: {} as RequestState,
        editBatch: {} as RequestState,
        validateBatch: {} as RequestState,
    };
}
