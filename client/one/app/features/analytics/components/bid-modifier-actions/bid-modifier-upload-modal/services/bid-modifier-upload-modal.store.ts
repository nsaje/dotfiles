import {Injectable, OnDestroy} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {Subject} from 'rxjs';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {BidModifiersService} from '../../../../../../core/bid-modifiers/services/bid-modifiers.service';
import {BidModifierUploadModalStoreState} from './bid-modifier-upload-modal.store.state';
import {takeUntil} from 'rxjs/operators';
import {HttpErrorResponse} from '@angular/common/http';
import * as endpointHelpers from '../../../../../../shared/helpers/endpoint.helpers';
import * as commonHelpers from '.././../../../../../shared/helpers/common.helpers';
import {Breakdown} from '../../../../../../app.constants';

@Injectable()
export class BidModifierUploadModalStore
    extends Store<BidModifierUploadModalStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<undefined> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor(private bidModifierService: BidModifiersService) {
        super(new BidModifierUploadModalStoreState());
        this.requestStateUpdater = endpointHelpers.getStoreRequestStateUpdater(
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
            fieldsErrors: {},
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
                        this.setState({
                            ...this.state,
                            fieldsErrors: {},
                        });
                        resolve();
                    },
                    (error: HttpErrorResponse) => {
                        this.setState({
                            ...this.state,
                            fieldsErrors: commonHelpers.isDefined(error.error)
                                ? commonHelpers.getValueOrDefault(
                                      error.error.details,
                                      {}
                                  )
                                : {},
                        });
                    }
                );
        });
    }
}
