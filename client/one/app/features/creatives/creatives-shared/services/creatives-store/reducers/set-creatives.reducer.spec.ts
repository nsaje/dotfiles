import {
    SetCreativesActionReducer,
    SetCreativesAction,
} from './set-creatives.reducer';
import {CreativesStoreState} from '../creatives.store.state';
import {AdType} from '../../../../../../app.constants';
import {
    TrackerEventType,
    TrackerMethod,
} from '../../../../../../core/creatives/creatives.constants';
import {Creative} from '../../../../../../core/creatives/types/creative';

describe('SetCreativesActionReducer', () => {
    let reducer: SetCreativesActionReducer;
    const mockedCreatives: Creative[] = [
        {
            id: '10000000',
            agencyId: '71',
            agencyName: 'Test agency',
            accountId: null,
            accountName: null,
            type: AdType.CONTENT,
            url: 'https://one.zemanta.com',
            title: 'Test',
            displayUrl: 'https://one.zemanta.com',
            brandName: 'Zemanta',
            description: 'Best advertising platform ever',
            callToAction: 'Advertise now!',
            tags: ['zemanta', 'native', 'advertising'],
            imageUrl: 'http://placekitten.com/200/300',
            iconUrl: 'http://placekitten.com/64/64',
            adTag: 'adTag',
            videoAssetId: '123',
            trackers: [
                {
                    eventType: TrackerEventType.IMPRESSION,
                    method: TrackerMethod.IMG,
                    url: 'https://test.com',
                    fallbackUrl: 'http://test.com',
                    trackerOptional: false,
                },
            ],
        },
        {
            id: '10000001',
            agencyId: '71',
            agencyName: 'Test agency',
            accountId: null,
            accountName: null,
            type: AdType.CONTENT,
            url: 'https://one.zemanta.com',
            title: 'Test 2',
            displayUrl: 'https://one.zemanta.com',
            brandName: 'Zemanta',
            description: 'Best advertising platform ever',
            callToAction: 'Advertise now!',
            tags: ['zemanta', 'native', 'advertising'],
            imageUrl: 'http://placekitten.com/200/300',
            iconUrl: 'http://placekitten.com/64/64',
            adTag: 'adTag',
            videoAssetId: '123',
            trackers: [
                {
                    eventType: TrackerEventType.IMPRESSION,
                    method: TrackerMethod.IMG,
                    url: 'https://test.com',
                    fallbackUrl: 'http://test.com',
                    trackerOptional: false,
                },
            ],
        },
    ];

    beforeEach(() => {
        reducer = new SetCreativesActionReducer();
    });

    it('should correctly reduce state', () => {
        const state = reducer.reduce(
            new CreativesStoreState(),
            new SetCreativesAction(mockedCreatives)
        );

        expect(state.entities).toEqual(mockedCreatives);
    });
});