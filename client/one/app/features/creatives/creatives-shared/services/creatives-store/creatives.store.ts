import {Injectable, Injector} from '@angular/core';
import {Store} from '../../../../../shared/services/store/store';
import {CreativesStoreState} from './creatives.store.state';
import {RequestStateUpdater} from '../../../../../shared/types/request-state-updater';
import {getStoreRequestStateUpdater} from '../../../../../shared/helpers/store.helpers';
import {CreativesService} from '../../../../../core/creatives/services/creatives.service';
import {StoreProvider} from '../../../../../shared/services/store/store.provider';
import {StoreAction} from '../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../shared/services/store/store.reducer';
import {StoreEffect} from '../../../../../shared/services/store/store.effect';
import {
    SetEntitiesAction,
    SetEntitiesActionReducer,
} from './reducers/set-entities.reducer';
import {
    FetchCreativesAction,
    FetchCreativesActionEffect,
} from './effects/fetch-creatives.effect';
import {
    SetScopeAction,
    SetScopeActionReducer,
} from './reducers/set-scope.reducer';
import {ScopeParams} from '../../../../../shared/types/scope-params';
import {CreativesSearchParams} from '../../types/creatives-search-params';
import {PaginationState} from '../../../../../shared/components/smart-grid/types/pagination-state';
import {CreativeTagsService} from '../../../../../core/creative-tags/services/creative-tags.service';
import {
    SetCreativeTagsAction,
    SetCreativeTagsActionReducer,
} from './reducers/set-creative-tags.reducer';
import {
    FetchCreativeTagsAction,
    FetchCreativeTagsActionEffect,
} from './effects/fetch-creative-tags.effect';
import {
    SetEntitySelectedAction,
    SetEntitySelectedActionReducer,
} from './reducers/set-entity-selected.reducer';
import {Creative} from '../../../../../core/creatives/types/creative';
import {AuthStore} from '../../../../../core/auth/services/auth.store';
import {isNotEmpty} from '../../../../../shared/helpers/common.helpers';
import {
    SetAllEntitiesSelectedAction,
    SetAllEntitiesSelectedActionReducer,
} from './reducers/set-all-entities-selected.reducer';

@Injectable()
export class CreativesStore extends Store<CreativesStoreState> {
    private requestStateUpdater: RequestStateUpdater;

    constructor(
        private creativesService: CreativesService,
        private creativeTagsService: CreativeTagsService,
        private authStore: AuthStore,
        injector: Injector
    ) {
        super(new CreativesStoreState(), injector);
        this.requestStateUpdater = getStoreRequestStateUpdater(this);
    }

    provide(): StoreProvider<
        StoreAction<any>,
        | StoreReducer<CreativesStoreState, StoreAction<any>>
        | StoreEffect<CreativesStoreState, StoreAction<any>>
    >[] {
        return [
            {
                provide: SetEntitiesAction,
                useClass: SetEntitiesActionReducer,
            },
            {
                provide: SetCreativeTagsAction,
                useClass: SetCreativeTagsActionReducer,
            },
            {
                provide: SetScopeAction,
                useClass: SetScopeActionReducer,
            },
            {
                provide: SetEntitySelectedAction,
                useClass: SetEntitySelectedActionReducer,
            },
            {
                provide: SetAllEntitiesSelectedAction,
                useClass: SetAllEntitiesSelectedActionReducer,
            },
            {
                provide: FetchCreativesAction,
                useClass: FetchCreativesActionEffect,
            },
            {
                provide: FetchCreativeTagsAction,
                useClass: FetchCreativeTagsActionEffect,
            },
        ];
    }

    setStore(
        scope: ScopeParams,
        pagination: PaginationState,
        searchParams: CreativesSearchParams
    ) {
        this.loadCreatives(scope, pagination, searchParams);
        this.loadTags(scope);
    }

    loadEntities(
        pagination: PaginationState,
        searchParams: CreativesSearchParams
    ) {
        this.loadCreatives(this.state.scope, pagination, searchParams);
    }

    isEntitySelected(entityId: string) {
        return this.state.selectedEntityIds.includes(entityId);
    }

    setEntitySelected(entityId: string, setSelected: boolean) {
        this.dispatch(new SetEntitySelectedAction({entityId, setSelected}));
    }

    areAllEntitiesSelected() {
        return (
            isNotEmpty(this.state.entities) &&
            this.state.entities
                .map(entity => entity.id)
                .every(this.isEntitySelected.bind(this))
        );
    }

    setAllEntitiesSelected(setSelected: boolean) {
        this.dispatch(new SetAllEntitiesSelectedAction(setSelected));
    }

    isReadOnly(creative: Creative): boolean {
        return this.authStore.hasReadOnlyAccessOn(
            this.state.scope.agencyId,
            creative.accountId
        );
    }

    private loadCreatives(
        scope: ScopeParams,
        pagination: PaginationState,
        searchParams: CreativesSearchParams
    ) {
        this.dispatch(
            new FetchCreativesAction({
                scope,
                pagination,
                searchParams,
                requestStateUpdater: this.requestStateUpdater,
            })
        );
    }

    private loadTags(scope: ScopeParams) {
        // TODO: Load only first 100 tags on store init, then load 100 matches when search keyword changes
        this.dispatch(
            new FetchCreativeTagsAction({
                scope,
                pagination: null,
                searchParams: null,
                requestStateUpdater: this.requestStateUpdater,
            })
        );
    }
}
