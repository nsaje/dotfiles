import {asapScheduler, of} from 'rxjs';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {CreativeTagsEndpoint} from './creative-tags.endpoint';
import {CreativeTagsService} from './creative-tags.service';

describe('CreativeTagsService', () => {
    let service: CreativeTagsService;
    let creativeTagsEndpointStub: jasmine.SpyObj<CreativeTagsEndpoint>;
    let requestStateUpdater: RequestStateUpdater;

    let mockedCreativeTag: string;
    let mockedCreativeTags: string[];
    let mockedAgencyId: string;
    let mockedAccountId: string;

    beforeEach(() => {
        creativeTagsEndpointStub = jasmine.createSpyObj(
            CreativeTagsEndpoint.name,
            ['list']
        );
        service = new CreativeTagsService(creativeTagsEndpointStub);
        requestStateUpdater = (requestName, requestState) => {};

        mockedAgencyId = '71';
        mockedAccountId = '55';
        mockedCreativeTags = ['abc', 'cde', 'def'];
        mockedCreativeTag = 'abc';
    });

    it('should get creativeTags via endpoint', () => {
        const limit = 10;
        const offset = 0;
        const keyword = 'blue';
        creativeTagsEndpointStub.list.and
            .returnValue(of(mockedCreativeTags, asapScheduler))
            .calls.reset();

        service
            .list(
                mockedAgencyId,
                mockedAccountId,
                offset,
                limit,
                keyword,
                requestStateUpdater
            )
            .subscribe(creativeTags => {
                expect(creativeTags).toEqual(mockedCreativeTags);
            });
        expect(creativeTagsEndpointStub.list).toHaveBeenCalledTimes(1);
        expect(creativeTagsEndpointStub.list).toHaveBeenCalledWith(
            mockedAgencyId,
            mockedAccountId,
            offset,
            limit,
            keyword,
            requestStateUpdater
        );
    });
});
