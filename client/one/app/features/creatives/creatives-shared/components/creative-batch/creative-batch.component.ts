import './creative-batch.component.less';

import * as deepEqual from 'fast-deep-equal';
import {
    ChangeDetectionStrategy,
    Component,
    Input,
    OnChanges,
    OnDestroy,
    OnInit,
} from '@angular/core';
import {CreativeBatchStore} from '../../services/creative-batch-store/creative-batch.store';
import {FetchCreativeBatchActionEffect} from '../../services/creative-batch-store/effects/fetch-creative-batch.effect';
import {CreateCreativeBatchActionEffect} from '../../services/creative-batch-store/effects/create-creative-batch.effect';
import {EditCreativeBatchActionEffect} from '../../services/creative-batch-store/effects/edit-creative-batch.effect';
import {ValidateCreativeBatchActionEffect} from '../../services/creative-batch-store/effects/validate-creative-batch.effect';
import {isDefined} from '../../../../../shared/helpers/common.helpers';
import {Subject, Observable} from 'rxjs';
import {
    distinctUntilChanged,
    filter,
    map,
    takeUntil,
    tap,
} from 'rxjs/operators';
import {FetchCreativeTagsActionEffect} from '../../services/creative-tags-store/effects/fetch-creative-tags.effect';
import {ScopeParams} from '../../../../../shared/types/scope-params';
import {CreativeTagsStore} from '../../services/creative-tags-store/creative-tags.store';
import {CreativeBatch} from '../../../../../core/creatives/types/creative-batch';
import {FetchCreativeCandidatesActionEffect} from '../../services/creative-batch-store/effects/fetch-creative-candidates.effect';
import {CreateCreativeCandidateActionEffect} from '../../services/creative-batch-store/effects/create-creative-candidate.effect';
import {EditCreativeCandidateActionEffect} from '../../services/creative-batch-store/effects/edit-creative-candidate.effect';
import {SetCandidatesActionReducer} from '../../services/creative-batch-store/reducers/set-candidates.reducer';
import {SetSelectedCandidateActionReducer} from '../../services/creative-batch-store/reducers/set-selected-candidate.reducer';
import {RemoveCreativeCandidateActionEffect} from '../../services/creative-batch-store/effects/remove-creative-candidate.effect';
import {SetCandidateErrorsActionReducer} from '../../services/creative-batch-store/reducers/set-candidate-errors.reducer';
import {CreativeCandidate} from '../../../../../core/creatives/types/creative-candidate';
import {AuthStore} from '../../../../../core/auth/services/auth.store';

@Component({
    selector: 'zem-creative-batch',
    templateUrl: './creative-batch.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [
        CreativeBatchStore,
        CreativeTagsStore,
        CreateCreativeBatchActionEffect,
        EditCreativeBatchActionEffect,
        FetchCreativeBatchActionEffect,
        ValidateCreativeBatchActionEffect,
        FetchCreativeTagsActionEffect,
        FetchCreativeCandidatesActionEffect,
        CreateCreativeCandidateActionEffect,
        EditCreativeCandidateActionEffect,
        SetCandidatesActionReducer,
        SetSelectedCandidateActionReducer,
        RemoveCreativeCandidateActionEffect,
        SetCandidateErrorsActionReducer,
    ],
})
export class CreativeBatchComponent implements OnInit, OnChanges, OnDestroy {
    @Input()
    batchId: string;

    canUseExtraTrackers: boolean = false;
    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: CreativeBatchStore,
        public tagsStore: CreativeTagsStore,
        public authStore: AuthStore
    ) {
        this.subscribeToStateUpdates();
    }

    ngOnInit() {
        this.canUseExtraTrackers = this.authStore.hasPermission(
            'zemauth.can_use_extra_trackers'
        );
    }

    ngOnChanges() {
        if (isDefined(this.batchId)) {
            this.store.loadEntity(this.batchId);
        }
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    onBatchNameChange($event: string) {
        this.store.updateBatchName($event);
    }

    onTagsSearch($event: string) {
        const batchScope: ScopeParams = this.getBatchScope(
            this.store.state.entity
        );
        this.tagsStore.loadTags(batchScope, $event);
    }

    trackCandidate(index: number, candidate: CreativeCandidate): string {
        return candidate.id;
    }

    private getBatchScope(batch: CreativeBatch): ScopeParams {
        return {
            agencyId: batch.agencyId,
            accountId: batch.accountId,
        };
    }

    private subscribeToStateUpdates() {
        this.getLoadTagsOnScopeChangeUpdater$()
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private getLoadTagsOnScopeChangeUpdater$(): Observable<CreativeBatch> {
        return this.store.state$.pipe(
            map(state => this.getBatchScope(state.entity)),
            filter(
                scope => isDefined(scope.agencyId) || isDefined(scope.accountId)
            ),
            distinctUntilChanged(deepEqual),
            tap(scope => {
                this.tagsStore.setStore(scope);
            })
        );
    }
}
