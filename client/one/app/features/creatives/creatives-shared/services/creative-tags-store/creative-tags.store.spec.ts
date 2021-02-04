import {fakeAsync, TestBed, tick} from '@angular/core/testing';
import {Injector} from '@angular/core';
import {ScopeParams} from '../../../../../shared/types/scope-params';
import {CreativeTagsService} from '../../../../../core/creative-tags/services/creative-tags.service';
import {
    FetchCreativeTagsAction,
    FetchCreativeTagsActionEffect,
} from '../creative-tags-store/effects/fetch-creative-tags.effect';
import {CreativeTagsStore} from './creative-tags.store';

describe('CreativeTagsStore', () => {
    let fetchCreativeTagsActionEffectStub: jasmine.SpyObj<FetchCreativeTagsActionEffect>;
    let creativeTagsServiceStub: jasmine.SpyObj<CreativeTagsService>;
    let store: CreativeTagsStore;

    beforeEach(() => {
        creativeTagsServiceStub = jasmine.createSpyObj(
            CreativeTagsService.name,
            ['list']
        );
        fetchCreativeTagsActionEffectStub = jasmine.createSpyObj(
            FetchCreativeTagsActionEffect.name,
            ['effect', 'dispatch']
        );
        TestBed.configureTestingModule({
            providers: [
                {
                    provide: FetchCreativeTagsActionEffect,
                    useValue: fetchCreativeTagsActionEffectStub,
                },
            ],
        });

        store = new CreativeTagsStore(TestBed.get(Injector));
    });

    it('should correctly initialize store', fakeAsync(() => {
        const mockedScopeParams: ScopeParams = {
            agencyId: '24',
            accountId: '367',
        };

        spyOn(store, 'dispatch').and.returnValue(Promise.resolve(true));

        store.setStore(mockedScopeParams);
        tick();

        expect(store.dispatch).toHaveBeenCalledTimes(1);
        expect(store.dispatch).toHaveBeenCalledWith(
            new FetchCreativeTagsAction({
                scope: mockedScopeParams,
                searchParams: {keyword: null},
                forceReload: true,
                requestStateUpdater: (<any>store).requestStateUpdater,
            })
        );
    }));

    it('should correctly load tags', fakeAsync(() => {
        const mockedScopeParams: ScopeParams = {
            agencyId: '24',
            accountId: '367',
        };

        spyOn(store, 'dispatch').and.returnValue(Promise.resolve(true));

        store.loadTags(mockedScopeParams, 'test');
        tick();

        expect(store.dispatch).toHaveBeenCalledTimes(1);
        expect(store.dispatch).toHaveBeenCalledWith(
            new FetchCreativeTagsAction({
                scope: mockedScopeParams,
                searchParams: {keyword: 'test'},
                forceReload: false,
                requestStateUpdater: (<any>store).requestStateUpdater,
            })
        );
    }));
});
