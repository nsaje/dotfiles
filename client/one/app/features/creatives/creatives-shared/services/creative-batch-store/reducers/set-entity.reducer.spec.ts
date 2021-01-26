import {SetEntityActionReducer} from './set-entity.reducer';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {CreativeBatch} from '../../../../../../core/creatives/types/creative-batch';
import {CreativeBatchStatus} from '../../../../../../core/creatives/types/creative-batch-status';
import {SetEntityAction} from './set-entity.reducer';

describe('SetEntityActionReducer', () => {
    let reducer: SetEntityActionReducer;
    const mockedBatch: CreativeBatch = {
        id: '1',
        agencyId: '2',
        accountId: null,
        name: 'test',
        status: CreativeBatchStatus.IN_PROGRESS,
        tags: [],
        imageCrop: null,
        displayUrl: null,
        brandName: null,
        description: null,
        callToAction: null,
        createdBy: null,
        createdDt: null,
    };

    beforeEach(() => {
        reducer = new SetEntityActionReducer();
    });

    it('should correctly set entity', () => {
        const state = reducer.reduce(
            new CreativeBatchStoreState(),
            new SetEntityAction(mockedBatch)
        );

        expect(state.entity).toEqual(mockedBatch);
    });
});
