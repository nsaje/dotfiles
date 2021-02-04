import './creatives.component.less';

import {
    ChangeDetectionStrategy,
    Component,
    EventEmitter,
    Input,
    OnChanges,
    OnDestroy,
    OnInit,
    Output,
    SimpleChanges,
} from '@angular/core';
import {ScopeParams} from '../../../../../shared/types/scope-params';
import {CreativesSearchParams} from '../../types/creatives-search-params';
import {PaginationState} from '../../../../../shared/components/smart-grid/types/pagination-state';
import {CreativesStore} from '../../services/creatives-store/creatives.store';
import {PaginationOptions} from '../../../../../shared/components/smart-grid/types/pagination-options';
import {DEFAULT_PAGINATION_OPTIONS} from '../../creatives-shared.config';
import * as deepEqual from 'fast-deep-equal';
import {FetchCreativesActionEffect} from '../../services/creatives-store/effects/fetch-creatives.effect';
import {isDefined} from '../../../../../shared/helpers/common.helpers';
import {FetchCreativeTagsActionEffect} from '../../services/creatives-store/effects/fetch-creative-tags.effect';
import {AuthStore} from '../../../../../core/auth/services/auth.store';
import {CreativeBatchStore} from '../../services/creative-batch-store/creative-batch.store';
import {merge, Observable, Subject} from 'rxjs';
import {
    distinctUntilChanged,
    filter,
    map,
    takeUntil,
    tap,
} from 'rxjs/operators';
import {CREATIVE_BATCH_PATH} from '../../../creatives.config';
import {Router} from '@angular/router';
import {FetchCreativeBatchActionEffect} from '../../services/creative-batch-store/effects/fetch-creative-batch.effect';
import {CreateCreativeBatchActionEffect} from '../../services/creative-batch-store/effects/create-creative-batch.effect';
import {EditCreativeBatchActionEffect} from '../../services/creative-batch-store/effects/edit-creative-batch.effect';
import {ValidateCreativeBatchActionEffect} from '../../services/creative-batch-store/effects/validate-creative-batch.effect';

@Component({
    selector: 'zem-creatives',
    templateUrl: './creatives.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [
        CreativesStore,
        CreativeBatchStore,
        FetchCreativesActionEffect,
        FetchCreativeTagsActionEffect,
        CreateCreativeBatchActionEffect,
        FetchCreativeBatchActionEffect,
        EditCreativeBatchActionEffect,
        ValidateCreativeBatchActionEffect,
    ],
})
export class CreativesComponent implements OnInit, OnChanges, OnDestroy {
    @Input()
    scopeParams: ScopeParams;
    @Input()
    searchParams: CreativesSearchParams;
    @Input()
    pagination: PaginationState;
    @Output()
    searchParamsChange: EventEmitter<CreativesSearchParams> = new EventEmitter<
        CreativesSearchParams
    >();
    @Output()
    paginationChange: EventEmitter<PaginationState> = new EventEmitter<
        PaginationState
    >();

    context: any;
    isReadOnly: boolean = true;
    paginationOptions: PaginationOptions = DEFAULT_PAGINATION_OPTIONS;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: CreativesStore,
        public batchStore: CreativeBatchStore,
        public authStore: AuthStore,
        private router: Router
    ) {
        this.context = {
            componentParent: this,
        };
    }

    ngOnInit(): void {
        this.subscribeToStateUpdates();
    }

    ngOnChanges(changes: SimpleChanges): void {
        this.paginationOptions = {
            ...DEFAULT_PAGINATION_OPTIONS,
            ...this.pagination,
        };

        if (isDefined(this.scopeParams?.agencyId)) {
            if (!deepEqual(this.scopeParams, this.store.state.scope)) {
                this.store.setStore(
                    this.scopeParams,
                    this.pagination,
                    this.searchParams
                );
            } else {
                this.store.loadEntities(this.pagination, this.searchParams);
            }
        }

        this.isReadOnly = this.authStore.hasReadOnlyAccessOn(
            this.scopeParams.agencyId,
            this.scopeParams.accountId
        );

        this.batchStore.state$.subscribe();
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    onBatchCreate() {
        this.batchStore.createEntity({
            accountId: this.scopeParams.accountId,
            agencyId: this.scopeParams.accountId
                ? null
                : this.scopeParams.agencyId,
        });
    }

    private subscribeToStateUpdates() {
        merge(this.createBatchCreatedUpdater$())
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private createBatchCreatedUpdater$(): Observable<string> {
        return this.batchStore.state$.pipe(
            map(state => state.entity?.id),
            filter(isDefined),
            distinctUntilChanged(),
            tap(batchId => {
                this.router.navigate([...CREATIVE_BATCH_PATH, batchId]);
            })
        );
    }
}
