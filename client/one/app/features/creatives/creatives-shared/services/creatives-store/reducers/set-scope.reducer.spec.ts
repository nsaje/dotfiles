import {SetScopeActionReducer, SetScopeAction} from './set-scope.reducer';
import {CreativesStoreState} from '../creatives.store.state';
import {ScopeParams} from '../../../../../../shared/types/scope-params';

describe('SetScopeActionReducer', () => {
    let reducer: SetScopeActionReducer;
    const mockedScopeParams: ScopeParams = {
        agencyId: '24',
        accountId: '367',
    };

    beforeEach(() => {
        reducer = new SetScopeActionReducer();
    });

    it('should correctly reduce state', () => {
        const state = reducer.reduce(
            new CreativesStoreState(),
            new SetScopeAction(mockedScopeParams)
        );

        expect(state.scope).toEqual(mockedScopeParams);
    });
});
