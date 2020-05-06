import {PublisherGroupsService} from '../../../../../../../../core/publisher-groups/services/publisher-groups.service';
import {AddToPublishersActionStore} from './add-to-publishers-action.store';
import {of} from 'rxjs';
import {PublisherInfo} from '../../../../../../../../core/publishers/types/publisher-info';
import {PublisherGroup} from '../../../../../../../../core/publisher-groups/types/publisher-group';

describe('AddToPublishersActionStore', () => {
    let serviceStub: jasmine.SpyObj<PublisherGroupsService>;
    let store: AddToPublishersActionStore;
    let mockedPublisherRows: PublisherInfo[] = [];
    let mockedPlacementRows: PublisherInfo[];
    let mockedAgencyLevelPublisherGroup: PublisherGroup;
    let mockedAccountLevelPublisherGroup: PublisherGroup;
    let expectedPublisherGroup: PublisherGroup;

    beforeEach(() => {
        serviceStub = jasmine.createSpyObj(PublisherGroupsService.name, [
            'search',
            'addEntries',
        ]);
        serviceStub.search.and.returnValue(of([]));
        serviceStub.addEntries.and.returnValue(
            of({name: 'test', defaultIncludeSubdomains: false, entries: []})
        );
        store = new AddToPublishersActionStore(serviceStub);

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

        mockedAccountLevelPublisherGroup = {
            id: '10000000',
            name: 'Account publisher group',
            agencyId: null,
            accountId: '222',
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

        mockedAgencyLevelPublisherGroup = {
            id: '10000001',
            name: 'Agency publisher group',
            agencyId: '111',
            accountId: null,
            includeSubdomains: false,
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
    });

    it('should correctly call search on the service', () => {
        store.search('123', 'test');

        expect(serviceStub.search).toHaveBeenCalledWith(
            null,
            '123',
            'test',
            0,
            10,
            false,
            jasmine.any(Function)
        );
    });

    it('should correctly call addEntries on the service for a newly created publisher group', () => {
        expectedPublisherGroup = {
            id: null,
            name: 'test',
            accountId: '123',
            agencyId: null,
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

        store.changeActiveEntity({
            target: store.state.activeEntity.entity,
            changes: {name: 'test', includeSubdomains: true},
        });
        store.save('123', mockedPublisherRows);

        expect(serviceStub.addEntries).toHaveBeenCalledWith(
            mockedPublisherRows,
            expectedPublisherGroup,
            jasmine.any(Function)
        );
    });

    it('should correctly call addEntries on the service for an existing account-level publisher group', () => {
        store.setActiveEntity(mockedAccountLevelPublisherGroup);
        store.save('123', mockedPublisherRows);

        expect(serviceStub.addEntries).toHaveBeenCalledWith(
            mockedPublisherRows,
            mockedAccountLevelPublisherGroup,
            jasmine.any(Function)
        );
    });

    it('should correctly call addEntries on the service for an existing agency-level publisher group', () => {
        store.setActiveEntity(mockedAgencyLevelPublisherGroup);
        store.save('123', mockedPublisherRows);

        expect(serviceStub.addEntries).toHaveBeenCalledWith(
            mockedPublisherRows,
            mockedAgencyLevelPublisherGroup,
            jasmine.any(Function)
        );
    });
});
