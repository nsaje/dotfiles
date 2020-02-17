import {asapScheduler, of} from 'rxjs';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {PublisherGroupsEndpoint} from './publisher-groups.endpoint';
import {PublisherGroupsService} from './publisher-groups.service';
import {PublisherGroup} from '../types/publisher-group';

describe('PublisherGroupsService', () => {
    let service: PublisherGroupsService;
    let publisherGroupsEndpointStub: jasmine.SpyObj<PublisherGroupsEndpoint>;
    let requestStateUpdater: RequestStateUpdater;

    let mockedPublisherGroups: PublisherGroup[];
    let mockedAgencyId: string;

    beforeEach(() => {
        publisherGroupsEndpointStub = jasmine.createSpyObj(
            PublisherGroupsEndpoint.name,
            ['search']
        );
        service = new PublisherGroupsService(publisherGroupsEndpointStub);
        requestStateUpdater = (requestName, requestState) => {};

        mockedAgencyId = '71';
        mockedPublisherGroups = [
            {
                id: '10000000',
                name: 'Test publisher group',
                agencyId: mockedAgencyId,
                accountId: null,
            },
        ];
    });

    it('should allow to search publisher groups via endpoint', () => {
        const limit = 10;
        const offset = 0;
        const keyword = 'blue';
        publisherGroupsEndpointStub.search.and
            .returnValue(of(mockedPublisherGroups, asapScheduler))
            .calls.reset();

        service
            .search(mockedAgencyId, keyword, offset, limit, requestStateUpdater)
            .subscribe(deals => {
                expect(deals).toEqual(mockedPublisherGroups);
            });
        expect(publisherGroupsEndpointStub.search).toHaveBeenCalledTimes(1);
        expect(publisherGroupsEndpointStub.search).toHaveBeenCalledWith(
            mockedAgencyId,
            keyword,
            offset,
            limit,
            requestStateUpdater
        );
    });
});
