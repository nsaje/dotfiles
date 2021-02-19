import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {Injectable} from '@angular/core';
import {StoreEffect} from '../../../../../../shared/services/store/store.effect';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {CreativeCandidate} from '../../../../../../core/creatives/types/creative-candidate';
import {takeUntil} from 'rxjs/operators';
import {SetCandidatesAction} from '../reducers/set-candidates.reducer';
import {SetSelectedCandidateAction} from '../reducers/set-selected-candidate.reducer';

export interface RemoveCreativeCandidateParams {
    candidate: CreativeCandidate;
    requestStateUpdater: RequestStateUpdater;
}

export class RemoveCreativeCandidateAction extends StoreAction<
    RemoveCreativeCandidateParams
> {}

// tslint:disable-next-line: max-classes-per-file
@Injectable()
export class RemoveCreativeCandidateActionEffect extends StoreEffect<
    CreativeBatchStoreState,
    RemoveCreativeCandidateAction
> {
    constructor(private service: CreativesService) {
        super();
    }

    effect(
        state: CreativeBatchStoreState,
        action: RemoveCreativeCandidateAction
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            const params: RemoveCreativeCandidateParams = action.payload;
            this.service
                .removeCandidate(
                    state.entity.id,
                    params.candidate.id,
                    params.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        this.dispatch(
                            new SetCandidatesAction(
                                state.candidates.filter(
                                    candidate => candidate !== params.candidate
                                )
                            )
                        );
                        if (state.selectedCandidateId === params.candidate.id) {
                            this.dispatch(
                                new SetSelectedCandidateAction(undefined)
                            );
                        }
                        // TODO: After https://github.com/Zemanta/zemanta-eins/pull/5623/files is merged, also remove this candidate's validation errors
                        resolve(true);
                    },
                    () => {
                        resolve(false);
                    }
                );
        });
    }
}
