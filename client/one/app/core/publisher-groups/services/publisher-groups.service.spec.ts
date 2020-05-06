import {asapScheduler, of} from 'rxjs';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {PublisherGroupsEndpoint} from './publisher-groups.endpoint';
import {PublisherGroupsService} from './publisher-groups.service';
import {PublisherGroup} from '../types/publisher-group';
import {PublisherInfo} from '../../publishers/types/publisher-info';
import {PublisherGroupWithEntries} from '../types/publisher-group-with-entries';

describe('PublisherGroupsService', () => {
    let service: PublisherGroupsService;
    let publisherGroupsEndpointStub: jasmine.SpyObj<PublisherGroupsEndpoint>;
    let requestStateUpdater: RequestStateUpdater;

    let mockedPublisherGroup: PublisherGroup;
    let mockedPublisherGroups: PublisherGroup[];
    let mockedPublisherRows: PublisherInfo[];
    let mockedPlacementRows: PublisherInfo[];
    let mockedAgencyId: string;
    let mockedAccountId: string;

    beforeEach(() => {
        publisherGroupsEndpointStub = jasmine.createSpyObj(
            PublisherGroupsEndpoint.name,
            ['search', 'list', 'upload', 'addEntries']
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

        mockedPublisherRows = [
            {
                sourceId: 12,
                sourceSlug: '12',
                publisher: 'www.zemanta.com',
            },
            {
                sourceId: 34,
                sourceSlug: '34',
                publisher: 'www.outbrain.com',
            },
        ];

        mockedPlacementRows = [
            {
                sourceId: 12,
                sourceSlug: '12',
                publisher: 'www.zemanta.com',
                placement: '00000000-0008-d469-0000-000000000106',
            },
            {
                sourceId: 34,
                sourceSlug: '34',
                publisher: 'www.outbrain.com',
                placement: '00000000-0008-d469-0000-000000000107',
            },
        ];
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
                true,
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
            true,
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

    it('should allow to add publisher entries to a publisher group', () => {
        const expectedRequest: PublisherGroupWithEntries = {
            id: '10000000',
            name: 'Test publisher group',
            accountId: '525',
            agencyId: '71',
            defaultIncludeSubdomains: false,
            entries: [
                {
                    source: '12',
                    publisher: 'www.zemanta.com',
                    includeSubdomains: false,
                },
                {
                    source: '34',
                    publisher: 'www.outbrain.com',
                    includeSubdomains: false,
                },
            ],
        };

        publisherGroupsEndpointStub.addEntries.and.returnValue(
            of(expectedRequest)
        );

        service.addEntries(
            mockedPublisherRows,
            mockedPublisherGroup,
            requestStateUpdater
        );

        expect(publisherGroupsEndpointStub.addEntries).toHaveBeenCalledWith(
            expectedRequest,
            requestStateUpdater
        );
    });

    it('should allow to add placement entries to a publisher group', () => {
        const expectedRequest: PublisherGroupWithEntries = {
            id: '10000000',
            name: 'Test publisher group',
            accountId: '525',
            agencyId: '71',
            defaultIncludeSubdomains: false,
            entries: [
                {
                    source: '12',
                    publisher: 'www.zemanta.com',
                    includeSubdomains: false,
                },
                {
                    source: '34',
                    publisher: 'www.outbrain.com',
                    includeSubdomains: false,
                },
            ],
        };

        publisherGroupsEndpointStub.addEntries.and.returnValue(
            of(expectedRequest)
        );

        service.addEntries(
            mockedPublisherRows,
            mockedPublisherGroup,
            requestStateUpdater
        );

        expect(publisherGroupsEndpointStub.addEntries).toHaveBeenCalledWith(
            expectedRequest,
            requestStateUpdater
        );
    });

    it('should allow to add entries to a newly created publisher group', () => {
        const newPublisherGroup: PublisherGroup = {
            id: null,
            name: 'A brand new publisher group',
            agencyId: null,
            accountId: mockedAccountId,
            includeSubdomains: true,
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

        const expectedRequest: PublisherGroupWithEntries = {
            id: null,
            name: 'A brand new publisher group',
            accountId: '525',
            agencyId: null,
            defaultIncludeSubdomains: true,
            entries: [
                {
                    source: '12',
                    publisher: 'www.zemanta.com',
                    includeSubdomains: true,
                },
                {
                    source: '34',
                    publisher: 'www.outbrain.com',
                    includeSubdomains: true,
                },
            ],
        };

        publisherGroupsEndpointStub.addEntries.and.returnValue(
            of(expectedRequest)
        );

        service.addEntries(
            mockedPublisherRows,
            newPublisherGroup,
            requestStateUpdater
        );

        expect(publisherGroupsEndpointStub.addEntries).toHaveBeenCalledWith(
            expectedRequest,
            requestStateUpdater
        );
    });
});
