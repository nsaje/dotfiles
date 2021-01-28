import {
    FetchCreativeTagsActionEffect,
    FetchCreativeTagsAction,
} from './fetch-creative-tags.effect';
import {of, asapScheduler} from 'rxjs';
import {SetCreativeTagsAction} from '../reducers/set-creative-tags.reducer';
import {fakeAsync, tick} from '@angular/core/testing';
import {CreativeTagsService} from '../../../../../../core/creative-tags/services/creative-tags.service';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {CreativesStoreState} from '../creatives.store.state';
import {ScopeParams} from '../../../../../../shared/types/scope-params';
import {CreativeTagsSearchParams} from '../../../types/creative-tags-search-params';
import {MAX_LOADED_TAGS} from '../../../creatives-shared.config';

function range(n: number): number[] {
    return [...Array(n).keys()];
}

describe('FetchCreativeTagsActionEffect', () => {
    let creativesServiceStub: jasmine.SpyObj<CreativeTagsService>;
    let mockedCreativeTags: string[];
    let mockedMaxCreativeTags: string[];
    let effect: FetchCreativeTagsActionEffect;
    let requestStateUpdater: RequestStateUpdater;

    function testEffect(
        scope: ScopeParams,
        searchParams: CreativeTagsSearchParams,
        forceReload: boolean,
        mockedResponse: string[],
        expectedResult: SetCreativeTagsAction,
        originalStoreState: CreativesStoreState,
        expectListCall: boolean
    ) {
        spyOn(effect, 'dispatch').and.returnValue(Promise.resolve(true));

        creativesServiceStub.list.and
            .returnValue(of(mockedResponse, asapScheduler))
            .calls.reset();

        effect.effect(
            originalStoreState,
            new FetchCreativeTagsAction({
                scope,
                searchParams,
                forceReload,
                requestStateUpdater: requestStateUpdater,
            })
        );
        tick();

        if (expectListCall) {
            expect(creativesServiceStub.list).toHaveBeenCalledTimes(1);
            expect(creativesServiceStub.list).toHaveBeenCalledWith(
                scope.agencyId,
                scope.accountId,
                0,
                MAX_LOADED_TAGS,
                searchParams.keyword,
                requestStateUpdater
            );

            expect(effect.dispatch).toHaveBeenCalledTimes(1);
            expect(effect.dispatch).toHaveBeenCalledWith(expectedResult);
        } else {
            expect(creativesServiceStub.list).toHaveBeenCalledTimes(0);
            expect(effect.dispatch).toHaveBeenCalledTimes(0);
        }
    }

    beforeEach(() => {
        creativesServiceStub = jasmine.createSpyObj(CreativeTagsService.name, [
            'list',
        ]);
        requestStateUpdater = (requestName, requestState) => {};

        effect = new FetchCreativeTagsActionEffect(creativesServiceStub);
        mockedCreativeTags = ['abc', 'cde', 'def'];
        mockedMaxCreativeTags = range(MAX_LOADED_TAGS).map(n => `test${n}`);
    });

    it('should fetch creative tags via service', fakeAsync(() => {
        const scope: ScopeParams = {agencyId: '65', accountId: '497'};
        const searchParams: CreativeTagsSearchParams = {
            keyword: 'test',
        };
        const expectedResult: SetCreativeTagsAction = new SetCreativeTagsAction(
            {
                tags: mockedCreativeTags,
                allTagsLoaded: false, // In this case we know that all tags could not have been loaded, because a keyword filter was used
            }
        );
        testEffect(
            scope,
            searchParams,
            false,
            mockedCreativeTags,
            expectedResult,
            new CreativesStoreState(),
            true
        );
    }));

    it('should determine that all tags have been loaded when searching without keyword', fakeAsync(() => {
        const scope: ScopeParams = {agencyId: '65', accountId: '497'};
        const searchParams: CreativeTagsSearchParams = {
            keyword: null,
        };
        const expectedResult: SetCreativeTagsAction = new SetCreativeTagsAction(
            {
                tags: mockedCreativeTags,
                allTagsLoaded: true,
            }
        );
        testEffect(
            scope,
            searchParams,
            false,
            mockedCreativeTags,
            expectedResult,
            new CreativesStoreState(),
            true
        );
    }));

    it('should determine that all tags have not been loaded when searching without keyword and max results are returned', fakeAsync(() => {
        const scope: ScopeParams = {agencyId: '65', accountId: '497'};
        const searchParams: CreativeTagsSearchParams = {
            keyword: null,
        };
        const expectedResult: SetCreativeTagsAction = new SetCreativeTagsAction(
            {
                tags: mockedMaxCreativeTags,
                allTagsLoaded: false,
            }
        );
        testEffect(
            scope,
            searchParams,
            false,
            mockedMaxCreativeTags,
            expectedResult,
            new CreativesStoreState(),
            true
        );
    }));

    it('should not fetch any tags if they have all already been loaded', fakeAsync(() => {
        const scope: ScopeParams = {agencyId: '65', accountId: '497'};
        const searchParams: CreativeTagsSearchParams = {
            keyword: 'test',
        };

        const storeStateWithLoadedTags: CreativesStoreState = new CreativesStoreState();
        storeStateWithLoadedTags.allTagsLoaded = true;

        testEffect(
            scope,
            searchParams,
            false,
            mockedCreativeTags,
            null,
            storeStateWithLoadedTags,
            false
        );
    }));

    it('should fetch tags even if they have all already been loaded when forceReload is set to true', fakeAsync(() => {
        const scope: ScopeParams = {agencyId: '65', accountId: '497'};
        const searchParams: CreativeTagsSearchParams = {
            keyword: 'test',
        };
        const expectedResult: SetCreativeTagsAction = new SetCreativeTagsAction(
            {
                tags: mockedCreativeTags,
                allTagsLoaded: false, // In this case we know that all tags could not have been loaded, because a keyword filter was used
            }
        );

        const storeStateWithLoadedTags: CreativesStoreState = new CreativesStoreState();
        storeStateWithLoadedTags.allTagsLoaded = true;

        testEffect(
            scope,
            searchParams,
            true,
            mockedCreativeTags,
            expectedResult,
            storeStateWithLoadedTags,
            true
        );
    }));
});
