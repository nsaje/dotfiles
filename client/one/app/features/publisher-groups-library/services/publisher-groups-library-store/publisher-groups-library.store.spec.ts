import {fakeAsync, tick} from '@angular/core/testing';
import {asapScheduler, of} from 'rxjs';
import {PublisherGroupsLibraryStore} from './publisher-groups-library.store';
import {PublisherGroupsService} from '../../../../core/publisher-groups/services/publisher-groups.service';
import {PublisherGroup} from '../../../../core/publisher-groups/types/publisher-group';

describe('PublisherGroupsLibraryStore', () => {
    let publisherGroupServiceStub: jasmine.SpyObj<PublisherGroupsService>;
    let store: PublisherGroupsLibraryStore;
    let mockedPublisherGroups: PublisherGroup[];
    let mockedAccountId: string;

    beforeEach(() => {
        publisherGroupServiceStub = jasmine.createSpyObj(
            PublisherGroupsService.name,
            ['list', 'upload', 'remove']
        );

        store = new PublisherGroupsLibraryStore(publisherGroupServiceStub);

        mockedPublisherGroups = [
            {
                id: '10000000',
                name: 'something.com',
                accountId: '525',
                agencyId: null,
                includeSubdomains: false,
                implicit: false,
                size: 3,
                modified: new Date(),
                created: new Date(),
                type: 'Blacklist',
                level: 'Campaign',
                levelName: 'Test campaign',
                levelId: 123456,
                entries: undefined,
            },
            {
                id: '10000000',
                name: 'test-group.com',
                accountId: '525',
                agencyId: null,
                includeSubdomains: false,
                implicit: false,
                size: 2,
                modified: new Date(),
                created: new Date(),
                type: null,
                level: null,
                levelName: '',
                levelId: null,
                entries: undefined,
            },
            {
                id: '10000001',
                name: 'hmm.si',
                accountId: '525',
                agencyId: null,
                includeSubdomains: false,
                implicit: false,
                size: 2,
                modified: new Date(),
                created: new Date(),
                type: null,
                level: null,
                levelName: '',
                levelId: null,
                entries: undefined,
            },
        ];

        mockedAccountId = '525';
    });

    it('should correctly initialize store', fakeAsync(() => {
        publisherGroupServiceStub.list.and
            .returnValue(of(mockedPublisherGroups, asapScheduler))
            .calls.reset();

        store.setStore(mockedAccountId);
        tick();

        expect(store.state.entities).toEqual(mockedPublisherGroups);
        expect(store.state.accountId).toEqual(mockedAccountId);
        expect(publisherGroupServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should list publisher groups via service', fakeAsync(() => {
        publisherGroupServiceStub.list.and
            .returnValue(of(mockedPublisherGroups, asapScheduler))
            .calls.reset();
        store.loadEntities();
        tick();

        expect(store.state.entities).toEqual(mockedPublisherGroups);
        expect(publisherGroupServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should upload publisher groups via service', fakeAsync(() => {
        publisherGroupServiceStub.upload.and
            .returnValue(of(mockedPublisherGroups[0], asapScheduler))
            .calls.reset();

        store.setActiveEntity(mockedPublisherGroups[0]);
        store.saveActiveEntity();
        tick();

        expect(publisherGroupServiceStub.upload).toHaveBeenCalledTimes(1);
        expect(publisherGroupServiceStub.upload).toHaveBeenCalledWith(
            mockedPublisherGroups[0],
            (<any>store).requestStateUpdater
        );
    }));

    it('should remove publisher group via service', fakeAsync(() => {
        const mockedPublisherGroupId = mockedPublisherGroups[0].id;
        publisherGroupServiceStub.remove.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();
        store.deleteEntity(mockedPublisherGroupId);
        tick();

        expect(publisherGroupServiceStub.remove).toHaveBeenCalledTimes(1);
        expect(publisherGroupServiceStub.remove).toHaveBeenCalledWith(
            mockedPublisherGroups[0].id,
            (<any>store).requestStateUpdater
        );
    }));
});
