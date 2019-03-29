import {Injectable, OnDestroy} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {Subject} from 'rxjs';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {BidModifiersService} from '../../../../../../core/bid-modifiers/services/bid-modifiers.service';
import {BidModifierUploadModalStoreState} from './bid-modifier-upload-modal.store.state';
import {takeUntil} from 'rxjs/operators';
import {HttpErrorResponse} from '@angular/common/http';
import * as storeHelpers from '../../../../../../shared/helpers/store.helpers';
import {Breakdown} from '../../../../../../app.constants';
import {BidModifierUploadModalStoreFieldsErrorsState} from './bid-modifier-upload-modal.store.fields-errors';

@Injectable()
export class BidModifierUploadModalStore
    extends Store<BidModifierUploadModalStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<undefined> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor(private bidModifierService: BidModifiersService) {
        super(new BidModifierUploadModalStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    init(adGroupId: number, breakdown: Breakdown): void {
        this.setState({
            ...this.state,
            adGroupId: adGroupId,
            breakdown: breakdown,
        });
    }

    updateFile(file: File): void {
        this.setState({
            ...this.state,
            file: file,
            fieldsErrors: new BidModifierUploadModalStoreFieldsErrorsState(),
        });
    }

    import(): Promise<void> {
        return new Promise<void>(resolve => {
            this.bidModifierService
                .importFromFile(
                    this.state.adGroupId,
                    this.state.breakdown,
                    this.state.file,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        this.updateState(
                            new BidModifierUploadModalStoreFieldsErrorsState(),
                            'fieldsErrors'
                        );
                        resolve();
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new BidModifierUploadModalStoreFieldsErrorsState(),
                            error
                        );
                        this.updateState(fieldsErrors, 'fieldsErrors');
                    }
                );
        });
    }
}
