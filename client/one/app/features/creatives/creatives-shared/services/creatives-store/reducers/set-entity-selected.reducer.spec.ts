import {
    SetEntitySelectedActionReducer,
    SetEntitySelectedAction,
} from './set-entity-selected.reducer';
import {Creative} from '../../../../../../core/creatives/types/creative';
import {CreativesStoreState} from '../creatives.store.state';
import {AdType} from '../../../../../../app.constants';

describe('SetEntitySelectedActionReducer', () => {
    let reducer: SetEntitySelectedActionReducer;
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
            displayHostedImageUrl: null,
            hostedImageUrl: null,
            landscapeHostedImageUrl: null,
            portraitHostedImageUrl: null,
            hostedIconUrl: null,
            imageWidth: null,
            imageHeight: null,
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
            displayHostedImageUrl: null,
            hostedImageUrl: null,
            landscapeHostedImageUrl: null,
            portraitHostedImageUrl: null,
            hostedIconUrl: null,
            imageWidth: null,
            imageHeight: null,
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
        reducer = new SetEntitySelectedActionReducer();
    });

    it('should correctly select an entity', () => {
        const state = reducer.reduce(
            mockedStoreState,
            new SetEntitySelectedAction({entityId: '2', setSelected: true})
        );

        expect(state.selectedEntityIds).toEqual(['1', '2']);
    });

    it('should correctly deselect an entity', () => {
        const state = reducer.reduce(
            mockedStoreState,
            new SetEntitySelectedAction({entityId: '1', setSelected: false})
        );

        expect(state.selectedEntityIds).toEqual([]);
    });

    it('should do nothing if entity to select is already selected', () => {
        const state = reducer.reduce(
            mockedStoreState,
            new SetEntitySelectedAction({entityId: '1', setSelected: true})
        );

        expect(state.selectedEntityIds).toEqual(['1']);
    });

    it('should do nothing if entity to deselect is already deselected', () => {
        const state = reducer.reduce(
            mockedStoreState,
            new SetEntitySelectedAction({entityId: '2', setSelected: false})
        );

        expect(state.selectedEntityIds).toEqual(['1']);
    });

    it('should not select a non-existent entity', () => {
        const state = reducer.reduce(
            mockedStoreState,
            new SetEntitySelectedAction({entityId: '3', setSelected: true})
        );

        expect(state.selectedEntityIds).toEqual(['1']);
    });
});
