import {Injectable, OnDestroy} from '@angular/core';
import {HttpErrorResponse} from '@angular/common/http';
import {Subject} from 'rxjs';
import {Store} from 'rxjs-observable-store';
import {takeUntil} from 'rxjs/operators';
import {Deal} from '../../../../core/deals/types/deal';
import {DealConnection} from '../../../../core/deals/types/deal-connection';
import {DealsLibraryStoreState} from './deals-library.store.state';
import {DealsLibraryStoreFieldsErrorsState} from './deals-library.store.fields-errors-state';
import {DealsService} from '../../../../core/deals/services/deals.service';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import * as storeHelpers from '../../../../shared/helpers/store.helpers';

@Injectable()
export class DealsLibraryStore extends Store<DealsLibraryStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor(private dealsService: DealsService) {
        super(new DealsLibraryStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
    }

    loadEntities(agencyId: string, page: number, pageSize: number) {
        return new Promise<void>((resolve, reject) => {
            const offset = this.getOffset(page, pageSize);
            this.dealsService
                .list(agencyId, offset, pageSize, this.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (deals: Deal[]) => {
                        this.patchState(deals, 'entities');
                        resolve();
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    saveActiveEntity(agencyId: string): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            this.dealsService
                .save(
                    agencyId,
                    this.state.activeEntity.entity,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        this.patchState(
                            new DealsLibraryStoreState().activeEntity.entity,
                            'activeEntity',
                            'entity'
                        );
                        resolve(true);
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new DealsLibraryStoreFieldsErrorsState(),
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

    validateActiveEntity(agencyId: string) {
        this.dealsService
            .validate(
                agencyId,
                this.state.activeEntity.entity,
                this.requestStateUpdater
            )
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                () => {
                    this.patchState(
                        new DealsLibraryStoreFieldsErrorsState(),
                        'activeEntity',
                        'fieldsErrors'
                    );
                },
                (error: HttpErrorResponse) => {
                    const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                        new DealsLibraryStoreFieldsErrorsState(),
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

    deleteActiveEntity(agencyId: string) {
        return new Promise<boolean>(resolve => {
            this.dealsService
                .remove(
                    agencyId,
                    this.state.activeEntity.entity.id,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        this.patchState(
                            new DealsLibraryStoreState().activeEntity.entity,
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

    // TODO set methods when activating connections in UI
    // loadActiveEntityConnections(agencyId: string) {
    //     this.dealsService
    //         .listConnections(
    //             agencyId,
    //             this.state.activeEntity.entity.id,
    //             this.requestStateUpdater
    //         )
    //         .pipe(takeUntil(this.ngUnsubscribe$))
    //         .subscribe(
    //             (connections: DealConnection[]) => {
    //                 this.patchState(connections, 'activeEntity', 'connections');
    //             },
    //             error => {}
    //         );
    // }
    //
    // deleteActiveEntityConnection(
    //     agencyId: string,
    //     dealId: string,
    //     dealConnectionId: string
    // ) {
    //     return new Promise<boolean>(resolve => {
    //         this.dealsService
    //             .removeConnection(
    //                 agencyId,
    //                 dealId,
    //                 dealConnectionId,
    //                 this.requestStateUpdater
    //             )
    //             .pipe(takeUntil(this.ngUnsubscribe$))
    //             .subscribe(
    //                 () => {
    //                     resolve(true);
    //                 },
    //                 error => {
    //                     resolve(false);
    //                 }
    //             );
    //     });
    // }

    setActiveEntity(entity: Deal) {
        this.patchState(entity, 'activeEntity', 'entity');
    }

    private getOffset(page: number, pageSize: number): number {
        return (page - 1) * pageSize;
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
