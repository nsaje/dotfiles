import {Injectable, OnDestroy} from '@angular/core';
import {HttpErrorResponse} from '@angular/common/http';
import {Subject} from 'rxjs';
import {Store} from 'rxjs-observable-store';
import {takeUntil} from 'rxjs/operators';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {Deal} from '../../../../core/deals/types/deal';
import {DealConnection} from '../../../../core/deals/types/deal-connection';
import {DealsLibraryStoreState} from './deals-library.store.state';
import {DealsLibraryStoreFieldsErrorsState} from './deals-library.store.fields-errors-state';
import {DealsService} from '../../../../core/deals/services/deals.service';
import {SourcesService} from '../../../../core/sources/services/sources.service';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import * as storeHelpers from '../../../../shared/helpers/store.helpers';

@Injectable()
export class DealsLibraryStore extends Store<DealsLibraryStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;
    private sourcesRequestStateUpdater: RequestStateUpdater;

    constructor(
        private dealsService: DealsService,
        private sourcesService: SourcesService
    ) {
        super(new DealsLibraryStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
        this.sourcesRequestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this,
            'sourcesRequests'
        );
    }

    initStore(
        agencyId: string,
        page: number,
        pageSize: number,
        keyword: string | null
    ): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.patchState(agencyId, 'agencyId');
            Promise.all([
                this.loadEntities(page, pageSize, keyword),
                this.loadSources(),
            ])
                .then(() => resolve())
                .catch(() => reject());
        });
    }

    loadEntities(
        page: number,
        pageSize: number,
        keyword: string | null = null
    ): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            const offset = this.getOffset(page, pageSize);
            this.dealsService
                .list(
                    this.state.agencyId,
                    offset,
                    pageSize,
                    keyword,
                    this.requestStateUpdater
                )
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

    saveActiveEntity(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.dealsService
                .save(
                    this.state.agencyId,
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
                        resolve();
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
                        reject();
                    }
                );
        });
    }

    validateActiveEntity(): void {
        const entity = storeHelpers.getNewStateWithoutNull(
            this.state.activeEntity.entity
        );
        this.dealsService
            .validate(this.state.agencyId, entity, this.requestStateUpdater)
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

    deleteEntity(dealId: string): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.dealsService
                .remove(this.state.agencyId, dealId, this.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        resolve();
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    loadActiveEntityConnections(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.dealsService
                .listConnections(
                    this.state.agencyId,
                    this.state.activeEntity.entity.id,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (connections: DealConnection[]) => {
                        this.patchState(
                            connections,
                            'activeEntity',
                            'connections'
                        );
                        resolve();
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    deleteActiveEntityConnection(dealConnectionId: string) {
        return new Promise<void>((resolve, reject) => {
            this.dealsService
                .removeConnection(
                    this.state.agencyId,
                    this.state.activeEntity.entity.id,
                    dealConnectionId,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        resolve();
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    setActiveEntity(entity: Partial<Deal>): void {
        const emptyActiveEntity = new DealsLibraryStoreState().activeEntity;
        this.setState({
            ...this.state,
            activeEntity: {
                ...emptyActiveEntity,
                entity: {
                    ...emptyActiveEntity.entity,
                    ...entity,
                },
            },
        });
    }

    changeActiveEntity(event: ChangeEvent<Deal>): void {
        this.patchState(
            {...event.target, ...event.changes},
            'activeEntity',
            'entity'
        );
        this.validateActiveEntity();
    }

    private loadSources(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.sourcesService
                .list(this.state.agencyId, this.sourcesRequestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    sources => {
                        this.patchState(sources, 'sources');
                        resolve();
                    },
                    () => {
                        reject();
                    }
                );
        });
    }

    private getOffset(page: number, pageSize: number): number {
        return (page - 1) * pageSize;
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
