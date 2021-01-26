import {SetFieldsErrorsActionReducer} from './set-fields-errors.reducer';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {SetFieldsErrorsAction} from './set-fields-errors.reducer';
import {CreativeBatchStoreFieldsErrorsState} from '../creative-batch.store.fields-errors-state';

describe('SetFieldsErrorsActionReducer', () => {
    let reducer: SetFieldsErrorsActionReducer;
    const mockedErrors: CreativeBatchStoreFieldsErrorsState = {
        id: [],
        agencyId: [],
        accountId: [],
        name: [],
        status: [],
        tags: [],
        imageCrop: [],
        displayUrl: [],
        brandName: [],
        description: [],
        callToAction: [],
        createdBy: [],
        createdDt: [],
        nonFieldErrors: [],
    };

    beforeEach(() => {
        reducer = new SetFieldsErrorsActionReducer();
    });

    it('should correctly set fieldsErrors', () => {
        const state = reducer.reduce(
            new CreativeBatchStoreState(),
            new SetFieldsErrorsAction(mockedErrors)
        );

        expect(state.fieldsErrors).toEqual(mockedErrors);
    });
});
