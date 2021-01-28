import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {Injectable} from '@angular/core';
import {StoreEffect} from '../../../../../../shared/services/store/store.effect';
import {CreativesStoreState} from '../creatives.store.state';
import {takeUntil} from 'rxjs/operators';
import {SetCreativeTagsAction} from '../reducers/set-creative-tags.reducer';
import {CreativeTagsService} from '../../../../../../core/creative-tags/services/creative-tags.service';
import {ScopeParams} from '../../../../../../shared/types/scope-params';
import {CreativeTagsSearchParams} from '../../../types/creative-tags-search-params';
import {isNotEmpty} from '../../../../../../shared/helpers/common.helpers';
import {MAX_LOADED_TAGS} from '../../../creatives-shared.config';

export interface FetchCreativeTagsParams {
    scope: ScopeParams;
    searchParams?: CreativeTagsSearchParams;
    forceReload: boolean;
    requestStateUpdater: RequestStateUpdater;
}

export class FetchCreativeTagsAction extends StoreAction<
    FetchCreativeTagsParams
> {}

// tslint:disable-next-line: max-classes-per-file
@Injectable()
export class FetchCreativeTagsActionEffect extends StoreEffect<
    CreativesStoreState,
    FetchCreativeTagsAction
> {
    constructor(private service: CreativeTagsService) {
        super();
    }

    effect(
        state: CreativesStoreState,
        action: FetchCreativeTagsAction
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            const params: FetchCreativeTagsParams = action.payload;
            if (state.allTagsLoaded && !params.forceReload) {
                resolve(true);
                return;
            }

            this.service
                .list(
                    params.scope.agencyId,
                    params.scope.accountId,
                    0,
                    MAX_LOADED_TAGS,
                    params.searchParams?.keyword,
                    params.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (creativeTags: string[]) => {
                        const allTagsLoaded: boolean =
                            !isNotEmpty(params.searchParams?.keyword) &&
                            creativeTags.length < MAX_LOADED_TAGS;
                        this.dispatch(
                            new SetCreativeTagsAction({
                                tags: creativeTags,
                                allTagsLoaded,
                            })
                        );
                        resolve(true);
                    },
                    () => {
                        resolve(false);
                    }
                );
        });
    }
}
