import {Injectable, OnDestroy} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {Subject} from 'rxjs';
import {RequestStateUpdater} from '../../../../../../../../shared/types/request-state-updater';
import {BidModifiersService} from '../../../../../../../../core/bid-modifiers/services/bid-modifiers.service';
import {BidModifierImportFormStoreState} from './bid-modifier-import-form.store.state';
import {takeUntil} from 'rxjs/operators';
import {HttpErrorResponse} from '@angular/common/http';
import * as storeHelpers from '../../../../../../../../shared/helpers/store.helpers';
import * as commonHelpers from '../../../../../../../../shared/helpers/common.helpers';
import {Breakdown} from '../../../../../../../../app.constants';
import {BidModifierImportFormStoreFieldsErrorsState} from './bid-modifier-import-form.store.fields-errors';

@Injectable()
export class BidModifierImportFormStore
    extends Store<BidModifierImportFormStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<undefined> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor(private bidModifierService: BidModifiersService) {
        super(new BidModifierImportFormStoreState());
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
            fieldsErrors: new BidModifierImportFormStoreFieldsErrorsState(),
        });
    }

    import(): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            if (!commonHelpers.isDefined(this.state.file)) {
                resolve(false);
                return;
            }
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
                        this.patchState(
                            new BidModifierImportFormStoreFieldsErrorsState(),
                            'fieldsErrors'
                        );
                        resolve(true);
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new BidModifierImportFormStoreFieldsErrorsState(),
                            error
                        );
                        this.patchState(fieldsErrors, 'fieldsErrors');
                        resolve(false);
                    }
                );
        });
    }
}
