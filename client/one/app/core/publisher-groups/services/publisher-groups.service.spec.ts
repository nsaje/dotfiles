import {asapScheduler, of} from 'rxjs';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {PublisherGroupsEndpoint} from './publisher-groups.endpoint';
import {PublisherGroupsService} from './publisher-groups.service';
import {PublisherGroup} from '../types/publisher-group';

describe('PublisherGroupsService', () => {
    let service: PublisherGroupsService;
    let publisherGroupsEndpointStub: jasmine.SpyObj<PublisherGroupsEndpoint>;
    let requestStateUpdater: RequestStateUpdater;

    let mockedPublisherGroup: PublisherGroup;
    let mockedPublisherGroups: PublisherGroup[];
    let mockedAgencyId: string;
    let mockedAccountId: string;

    beforeEach(() => {
        publisherGroupsEndpointStub = jasmine.createSpyObj(
            PublisherGroupsEndpoint.name,
            ['search', 'list', 'upload']
        );
        service = new PublisherGroupsService(publisherGroupsEndpointStub);
        requestStateUpdater = (requestName, requestState) => {};

        mockedAgencyId = '71';
        mockedAccountId = '525';
        mockedPublisherGroup = {
            id: '10000000',
            name: 'Test publisher group',
            agencyId: mockedAgencyId,
            accountId: mockedAccountId,
            includeSubdomains: null,
            implicit: null,
            size: null,
            modified: null,
            created: null,
            type: null,
            level: null,
            levelName: null,
            levelId: null,
            entries: null,
        };
        mockedPublisherGroups = [mockedPublisherGroup];
    });

    it('should allow to search publisher groups via endpoint', () => {
        const limit = 10;
        const offset = 0;
        const keyword = 'blue';
        publisherGroupsEndpointStub.search.and
            .returnValue(of(mockedPublisherGroups, asapScheduler))
            .calls.reset();

        service
            .search(
                mockedAgencyId,
                null,
                keyword,
                offset,
                limit,
                requestStateUpdater
            )
            .subscribe(publisherGroups => {
                expect(publisherGroups).toEqual(mockedPublisherGroups);
            });
        expect(publisherGroupsEndpointStub.search).toHaveBeenCalledTimes(1);
        expect(publisherGroupsEndpointStub.search).toHaveBeenCalledWith(
            mockedAgencyId,
            null,
            keyword,
            offset,
            limit,
            requestStateUpdater
        );
    });

    it('should allow to read list of publisher groups via endpoint', () => {
        publisherGroupsEndpointStub.list.and
            .returnValue(of(mockedPublisherGroups, asapScheduler))
            .calls.reset();

        service
            .list(null, mockedAccountId, requestStateUpdater)
            .subscribe(publisherGroups => {
                expect(publisherGroups).toEqual(mockedPublisherGroups);
            });
        expect(publisherGroupsEndpointStub.list).toHaveBeenCalledTimes(1);
        expect(publisherGroupsEndpointStub.list).toHaveBeenCalledWith(
            null,
            mockedAccountId,
            requestStateUpdater
        );
    });

    it('should allow to save a publisher group via endpoint', () => {
        publisherGroupsEndpointStub.upload.and
            .returnValue(of(mockedPublisherGroup, asapScheduler))
            .calls.reset();

        service
            .upload(mockedPublisherGroup, requestStateUpdater)
            .subscribe(publisherGroups => {
                expect(publisherGroups).toEqual(mockedPublisherGroup);
            });
        expect(publisherGroupsEndpointStub.upload).toHaveBeenCalledTimes(1);
        expect(publisherGroupsEndpointStub.upload).toHaveBeenCalledWith(
            mockedPublisherGroup,
            requestStateUpdater
        );
    });
});
