import {asapScheduler, of} from 'rxjs';
import * as clone from 'clone';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {CreativesEndpoint} from './creatives.endpoint';
import {CreativesService} from './creatives.service';
import {Creative} from '../types/creative';
import {AdType} from '../../../app.constants';
import {TrackerEventType, TrackerMethod} from '../creatives.constants';

describe('CreativesService', () => {
    let service: CreativesService;
    let creativesEndpointStub: jasmine.SpyObj<CreativesEndpoint>;
    let requestStateUpdater: RequestStateUpdater;

    let mockedCreative: Creative;
    let mockedCreatives: Creative[];
    let mockedAgencyId: string;
    let mockedAccountId: string;

    beforeEach(() => {
        creativesEndpointStub = jasmine.createSpyObj(CreativesEndpoint.name, [
            'list',
        ]);
        service = new CreativesService(creativesEndpointStub);
        requestStateUpdater = (requestName, requestState) => {};

        mockedAgencyId = '71';
        mockedAccountId = '55';
        mockedCreatives = [
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
        ];
        mockedCreative = clone(mockedCreatives[0]);
    });

    it('should get creatives via endpoint', () => {
        const limit = 10;
        const offset = 0;
        const keyword = 'blue';
        const agencyOnly = true;
        const creativeType = AdType.CONTENT;
        const tags = ['a', 'b', 'c'];
        creativesEndpointStub.list.and
            .returnValue(of(mockedCreatives, asapScheduler))
            .calls.reset();

        service
            .list(
                mockedAgencyId,
                mockedAccountId,
                offset,
                limit,
                keyword,
                creativeType,
                tags,
                requestStateUpdater
            )
            .subscribe(creatives => {
                expect(creatives).toEqual(mockedCreatives);
            });
        expect(creativesEndpointStub.list).toHaveBeenCalledTimes(1);
        expect(creativesEndpointStub.list).toHaveBeenCalledWith(
            mockedAgencyId,
            mockedAccountId,
            offset,
            limit,
            keyword,
            creativeType,
            tags,
            requestStateUpdater
        );
    });
});
