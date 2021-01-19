import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {Injectable} from '@angular/core';
import {StoreEffect} from '../../../../../../shared/services/store/store.effect';
import {CreativesStoreState} from '../creatives.store.state';
import {takeUntil} from 'rxjs/operators';
import {SetCreativeTagsAction} from '../reducers/set-creative-tags.reducer';
import {getOffset} from '../../../../../../shared/helpers/pagination.helper';
import {CreativeTagsService} from '../../../../../../core/creative-tags/services/creative-tags.service';
import {ScopeParams} from '../../../../../../shared/types/scope-params';
import {CreativeTagsSearchParams} from '../../../types/creative-tags-search-params';
import {PaginationState} from '../../../../../../shared/components/smart-grid/types/pagination-state';

export interface FetchCreativeTagsParams {
    scope: ScopeParams;
    pagination?: PaginationState;
    searchParams?: CreativeTagsSearchParams;
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
            const offset: number = params.pagination
                ? getOffset(params.pagination.page, params.pagination.pageSize)
                : null;
            this.service
                .list(
                    params.scope.agencyId,
                    params.scope.accountId,
                    offset,
                    params.pagination?.pageSize,
                    params.searchParams?.keyword,
                    params.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (creativeTags: string[]) => {
                        this.dispatch(new SetCreativeTagsAction(creativeTags));
                        resolve(true);
                    },
                    () => {
                        resolve(false);
                    }
                );
        });
    }
}
