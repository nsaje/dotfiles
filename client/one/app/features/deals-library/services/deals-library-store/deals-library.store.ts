import {Injectable, OnDestroy} from '@angular/core';
import {HttpErrorResponse} from '@angular/common/http';
import {Subject} from 'rxjs';
import {Store} from 'rxjs-observable-store';
import {takeUntil} from 'rxjs/operators';
import {Deal} from '../../../../core/deals/types/deal';
import {DealConnection} from '../../../../core/deals/types/deal-connection';
import {DealsStoreState} from './deals-library.store.state';
import {DealStoreFieldsErrorsState} from './deals-library.store.fields-errors-state';
import {DealsService} from '../../../../core/deals/services/deals.service';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import * as storeHelpers from '../../../../shared/helpers/store.helpers';

@Injectable()
export class DealsStore extends Store<DealsStoreState> implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor(private dealsService: DealsService) {
        super(new DealsStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
    }

    loadEntities(agencyId: string, page: number, pageSize: number) {
        const offset = this.getOffset(page, pageSize);
        this.dealsService
            .list(agencyId, offset, pageSize, this.requestStateUpdater)
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                (deals: Deal[]) => {
                    this.patchState(deals, 'entities');
                },
                error => {}
            );
    }

    saveActiveEntity(
        agencyId: string,
        dealId: string,
        deal: Deal
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            this.dealsService
                .save(agencyId, dealId, deal, this.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        this.patchState(
                            new DealsStoreState().activeEntity.entity,
                            'activeEntity',
                            'entity'
                        );
                        resolve(true);
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new DealStoreFieldsErrorsState(),
                            error
                        );
                        this.patchState(
                            fieldsErrors,
                            'activeEntity',
                            'fieldsErrors'
                        );
                        resolve(false);
                    }
                );
        });
    }

    validateActiveEntity(agencyId: string, activeEntity: Partial<Deal>) {
        this.dealsService
            .validate(agencyId, activeEntity, this.requestStateUpdater)
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                () => {
                    this.patchState(
                        new DealStoreFieldsErrorsState(),
                        'activeEntity',
                        'fieldsErrors'
                    );
                },
                (error: HttpErrorResponse) => {
                    const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                        new DealStoreFieldsErrorsState(),
                        error
                    );
                    this.patchState(
                        fieldsErrors,
                        'activeEntity',
                        'fieldsErrors'
                    );
                }
            );
    }

    loadActiveEntity(agencyId: string, dealId: string) {
        this.dealsService
            .get(agencyId, dealId, this.requestStateUpdater)
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                (deal: Deal) => {
                    this.patchState(deal, 'activeEntity', 'entity');
                },
                error => {}
            );
    }

    deleteActiveEntity(agencyId: string, dealId: string) {
        return new Promise<boolean>(resolve => {
            this.dealsService
                .remove(agencyId, dealId, this.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        this.patchState(
                            new DealsStoreState().activeEntity.entity,
                            'activeEntity',
                            'entity'
                        );
                        resolve(true);
                    },
                    error => {
                        resolve(false);
                    }
                );
        });
    }

    loadConnections(agencyId: string, dealId: string) {
        this.dealsService
            .listConnections(agencyId, dealId, this.requestStateUpdater)
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                (connections: DealConnection[]) => {
                    this.patchState(connections, 'activeEntity', 'connections');
                },
                error => {}
            );
    }

    deleteConnection(
        agencyId: string,
        dealId: string,
        dealConnectionId: string
    ) {
        return new Promise<boolean>(resolve => {
            this.dealsService
                .removeConnection(
                    agencyId,
                    dealId,
                    dealConnectionId,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        resolve(true);
                    },
                    error => {
                        resolve(false);
                    }
                );
        });
    }

    setActiveEntity(entity: Deal) {
        this.patchState(entity, 'activeEntity', 'entity');
    }

    private getOffset(page: number, pageSize: number): number {
        return page - 1 * pageSize;
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
