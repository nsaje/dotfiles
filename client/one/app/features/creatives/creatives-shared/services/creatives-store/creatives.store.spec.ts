import {fakeAsync, TestBed, tick} from '@angular/core/testing';
import {asapScheduler, of} from 'rxjs';
import {CreativesService} from '../../../../../core/creatives/services/creatives.service';
import {AuthStore} from '../../../../../core/auth/services/auth.store';
import {CreativesStore} from './creatives.store';
import {Creative} from '../../../../../core/creatives/types/creative';
import {Injector} from '@angular/core';
import {
    FetchCreativesAction,
    FetchCreativesActionEffect,
} from './effects/fetch-creatives.effect';
import {AdType} from '../../../../../app.constants';
import {ScopeParams} from '../../../../../shared/types/scope-params';
import {PaginationState} from '../../../../../shared/components/smart-grid/types/pagination-state';
import {CreativesSearchParams} from '../../types/creatives-search-params';
import {CreativesStoreState} from './creatives.store.state';
import {CreativeTagsService} from '../../../../../core/creative-tags/services/creative-tags.service';
import {
    FetchCreativeTagsAction,
    FetchCreativeTagsActionEffect,
} from './effects/fetch-creative-tags.effect';

describe('CreativesLibraryStore', () => {
    let fetchCreativesActionEffectStub: jasmine.SpyObj<FetchCreativesActionEffect>;
    let fetchCreativeTagsActionEffectStub: jasmine.SpyObj<FetchCreativeTagsActionEffect>;
    let creativesServiceStub: jasmine.SpyObj<CreativesService>;
    let creativeTagsServiceStub: jasmine.SpyObj<CreativeTagsService>;
    let authStoreStub: jasmine.SpyObj<AuthStore>;
    let store: CreativesStore;

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

    beforeEach(() => {
        creativesServiceStub = jasmine.createSpyObj(CreativesService.name, [
            'list',
        ]);
        creativeTagsServiceStub = jasmine.createSpyObj(
            CreativeTagsService.name,
            ['list']
        );
        authStoreStub = jasmine.createSpyObj(AuthStore.name, [
            'hasAgencyScope',
            'hasReadOnlyAccessOn',
        ]);
        fetchCreativesActionEffectStub = jasmine.createSpyObj(
            FetchCreativesActionEffect.name,
            ['effect', 'dispatch']
        );
        fetchCreativeTagsActionEffectStub = jasmine.createSpyObj(
            FetchCreativesActionEffect.name,
            ['effect', 'dispatch']
        );
        TestBed.configureTestingModule({
            providers: [
                {
                    provide: FetchCreativesActionEffect,
                    useValue: fetchCreativesActionEffectStub,
                },
                {
                    provide: FetchCreativeTagsActionEffect,
                    useValue: fetchCreativeTagsActionEffectStub,
                },
            ],
        });

        store = new CreativesStore(
            creativesServiceStub,
            creativeTagsServiceStub,
            authStoreStub,
            TestBed.get(Injector)
        );
    });

    it('should correctly initialize store', fakeAsync(() => {
        const mockedScopeParams: ScopeParams = {
            agencyId: '24',
            accountId: '367',
        };
        const mockedPagination: PaginationState = {
            page: 1,
            pageSize: 10,
        };
        const mockedSearchParams: CreativesSearchParams = {
            keyword: 'test',
            tags: ['a', 'b', 'c'],
            creativeType: AdType.AD_TAG,
        };

        spyOn(store, 'dispatch').and.returnValue(Promise.resolve(true));
        creativesServiceStub.list.and
            .returnValue(of(mockedEntities, asapScheduler))
            .calls.reset();

        store.setStore(mockedScopeParams, mockedPagination, mockedSearchParams);
        tick();

        expect(store.dispatch).toHaveBeenCalledTimes(2);
        expect(store.dispatch).toHaveBeenCalledWith(
            new FetchCreativesAction({
                scope: mockedScopeParams,
                pagination: mockedPagination,
                searchParams: mockedSearchParams,
                requestStateUpdater: (<any>store).requestStateUpdater,
            })
        );
        expect(store.dispatch).toHaveBeenCalledWith(
            new FetchCreativeTagsAction({
                scope: mockedScopeParams,
                pagination: null,
                searchParams: null,
                requestStateUpdater: (<any>store).requestStateUpdater,
            })
        );
    }));

    it('should know if an entity is selected', fakeAsync(() => {
        store.setState({
            ...new CreativesStoreState(),
            entities: mockedEntities,
            selectedEntityIds: ['1'],
        });

        expect(store.isEntitySelected('1')).toBeTrue();
        expect(store.isEntitySelected('2')).toBeFalse();
        expect(store.isEntitySelected('3')).toBeFalse();
    }));

    it('should know if all entities are selected', fakeAsync(() => {
        store.setState({
            ...new CreativesStoreState(),
            entities: mockedEntities,
            selectedEntityIds: ['1'],
        });

        expect(store.areAllEntitiesSelected()).toBeFalse();

        store.setState({
            ...new CreativesStoreState(),
            entities: mockedEntities,
            selectedEntityIds: ['1', '2'],
        });

        expect(store.areAllEntitiesSelected()).toBeTrue();

        store.setState({
            ...new CreativesStoreState(),
            entities: mockedEntities,
            selectedEntityIds: ['1', '3'],
        });

        expect(store.areAllEntitiesSelected()).toBeFalse();
    }));
});
