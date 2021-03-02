import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {Injectable} from '@angular/core';
import {StoreEffect} from '../../../../../../shared/services/store/store.effect';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {CreativeCandidate} from '../../../../../../core/creatives/types/creative-candidate';
import {takeUntil} from 'rxjs/operators';
import {SetCandidatesAction} from '../reducers/set-candidates.reducer';
import {replaceArrayItem} from '../../../../../../shared/helpers/array.helpers';
import {SetCandidateErrorsAction} from '../reducers/set-candidate-errors.reducer';
import {HttpErrorResponse} from '@angular/common/http';
import * as storeHelpers from '../../../../../../shared/helpers/store.helpers';
import {CreativeCandidateFieldsErrorsState} from '../../../types/creative-candidate-fields-errors-state';
import {AD_SIZES} from '../../../creatives-shared.config';
import {AdSizeConfig} from '../../../types/ad-size-config';
import {isDefined} from '../../../../../../shared/helpers/common.helpers';

export interface EditCreativeCandidateParams {
    candidate: CreativeCandidate;
    changes: Partial<CreativeCandidate>;
    requestStateUpdater: RequestStateUpdater;
}

export class EditCreativeCandidateAction extends StoreAction<
    EditCreativeCandidateParams
> {}

// tslint:disable-next-line: max-classes-per-file
@Injectable()
export class EditCreativeCandidateActionEffect extends StoreEffect<
    CreativeBatchStoreState,
    EditCreativeCandidateAction
> {
    constructor(private service: CreativesService) {
        super();
    }

    effect(
        state: CreativeBatchStoreState,
        action: EditCreativeCandidateAction
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            const params: EditCreativeCandidateParams = action.payload;
            this.service
                .editCandidate(
                    state.entity.id,
                    params.candidate.id,
                    {
                        type: params.candidate.type,
                        ...this.mapCandidateToBackend(params.changes),
                    },
                    params.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (candidate: CreativeCandidate) => {
                        this.setCandidateState(state, candidate);
                        this.setCandidateErrors(
                            params.candidate,
                            new CreativeCandidateFieldsErrorsState()
                        );
                        resolve(true);
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new CreativeCandidateFieldsErrorsState(),
                            error
                        );
                        this.setCandidateState(state, params.candidate);
                        this.setCandidateErrors(params.candidate, fieldsErrors);
                        resolve(false);
                    }
                );
        });
    }

    private setCandidateState(
        state: CreativeBatchStoreState,
        candidate: CreativeCandidate
    ) {
        this.dispatch(
            new SetCandidatesAction(
                replaceArrayItem(
                    state.candidates,
                    (candidate: CreativeCandidate) => candidate.id,
                    candidate
                )
            )
        );
    }

    private setCandidateErrors(
        candidate: CreativeCandidate,
        fieldsErrors: CreativeCandidateFieldsErrorsState
    ) {
        this.dispatch(
            new SetCandidateErrorsAction({
                candidateId: candidate.id,
                fieldsErrors,
            })
        );
    }

    private mapCandidateToBackend(
        candidate: Partial<CreativeCandidate>
    ): Partial<CreativeCandidate> {
        const result: Partial<CreativeCandidate> = {...candidate};
        if (isDefined(candidate.size)) {
            const dimensions: AdSizeConfig = AD_SIZES.find(
                x => x.size === candidate.size
            );
            delete result.size;
            result.imageWidth = dimensions.width;
            result.imageHeight = dimensions.height;
        }
        return result;
    }
}
