import {
    SetCreativeTagsActionReducer,
    SetCreativeTagsAction,
} from './set-creative-tags.reducer';
import {CreativesStoreState} from '../creatives.store.state';

describe('SetCreativeTagsActionReducer', () => {
    let reducer: SetCreativeTagsActionReducer;
    const mockedCreativeTags: string[] = ['abc', 'cde', 'def'];

    beforeEach(() => {
        reducer = new SetCreativeTagsActionReducer();
    });

    it('should correctly reduce state', () => {
        const state = reducer.reduce(
            new CreativesStoreState(),
            new SetCreativeTagsAction(mockedCreativeTags)
        );

        expect(state.availableTags).toEqual(mockedCreativeTags);
    });
});
