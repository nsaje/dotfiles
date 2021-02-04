import {
    SetAvailableTagsActionReducer,
    SetAvailableTagsAction,
} from './set-available-tags.reducer';
import {CreativeTagsStoreState} from '../creative-tags-store.state';

describe('SetAvailableTagsActionReducer', () => {
    let reducer: SetAvailableTagsActionReducer;
    const mockedNewState1: CreativeTagsStoreState = {
        ...new CreativeTagsStoreState(),
        availableTags: ['abc', 'cde', 'def'],
        allTagsLoaded: false,
    };
    const mockedNewState2: CreativeTagsStoreState = {
        ...new CreativeTagsStoreState(),
        availableTags: [],
        allTagsLoaded: true,
    };

    beforeEach(() => {
        reducer = new SetAvailableTagsActionReducer();
    });

    it('should correctly reduce state', () => {
        const state1 = reducer.reduce(
            new CreativeTagsStoreState(),
            new SetAvailableTagsAction(mockedNewState1)
        );

        expect(state1.availableTags).toEqual(mockedNewState1.availableTags);
        expect(state1.allTagsLoaded).toEqual(mockedNewState1.allTagsLoaded);

        const state2 = reducer.reduce(
            new CreativeTagsStoreState(),
            new SetAvailableTagsAction(mockedNewState2)
        );

        expect(state2.availableTags).toEqual(mockedNewState2.availableTags);
        expect(state2.allTagsLoaded).toEqual(mockedNewState2.allTagsLoaded);
    });
});
