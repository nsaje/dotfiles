import {
    SetAllEntitiesSelectedActionReducer,
    SetAllEntitiesSelectedAction,
} from './set-all-entities-selected.reducer';
import {CreativesStoreState} from '../creatives.store.state';
import {Creative} from '../../../../../../core/creatives/types/creative';
import {AdType} from '../../../../../../app.constants';

describe('SetAllEntitiesSelectedActionReducer', () => {
    let reducer: SetAllEntitiesSelectedActionReducer;
    const mockedEntities: Creative[] = [
        {
            id: '1',
            agencyId: null,
            agencyName: null,
            accountId: null,
            accountName: null,
            type: AdType.AD_TAG,
            url: 'x',
            title: null,
            displayUrl: 'y',
            brandName: null,
            description: null,
            callToAction: null,
            tags: [],
            imageUrl: null,
            iconUrl: null,
            adTag: null,
            videoAssetId: null,
            trackers: [],
        },
        {
            id: '2',
            agencyId: null,
            agencyName: null,
            accountId: null,
            accountName: null,
            type: AdType.AD_TAG,
            url: 'x',
            title: null,
            displayUrl: 'y',
            brandName: null,
            description: null,
            callToAction: null,
            tags: [],
            imageUrl: null,
            iconUrl: null,
            adTag: null,
            videoAssetId: null,
            trackers: [],
        },
    ];

    let mockedStoreState: CreativesStoreState = new CreativesStoreState();
    mockedStoreState = {
        ...mockedStoreState,
        entities: mockedEntities,
        selectedEntityIds: ['1'],
    };

    beforeEach(() => {
        reducer = new SetAllEntitiesSelectedActionReducer();
    });

    it('should correctly select all entities', () => {
        const state = reducer.reduce(
            mockedStoreState,
            new SetAllEntitiesSelectedAction(true)
        );

        expect(state.selectedEntityIds).toEqual(['1', '2']);
    });

    it('should correctly deselect all entities', () => {
        const state = reducer.reduce(
            mockedStoreState,
            new SetAllEntitiesSelectedAction(false)
        );

        expect(state.selectedEntityIds).toEqual([]);
    });
});
