import {Injectable, OnDestroy} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {takeUntil} from 'rxjs/operators';
import {PublisherGroupsService} from '../../../../core/publisher-groups/services/publisher-groups.service';
import {Subject} from 'rxjs';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {PublisherGroupsLibraryStoreState} from './publisher-groups-library.store.state';
import {PublisherGroup} from '../../../../core/publisher-groups/types/publisher-group';
import {HttpErrorResponse} from '@angular/common/http';
import * as storeHelpers from '../../../../shared/helpers/store.helpers';
import {PublisherGroupsLibraryStoreFieldsErrorsState} from './publisher-groups-library.store.fields-errors-state';
import {ChangeEvent} from '../../../../shared/types/change-event';

@Injectable()
export class PublisherGroupsLibraryStore
    extends Store<PublisherGroupsLibraryStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor(private publisherGroupsService: PublisherGroupsService) {
        super(new PublisherGroupsLibraryStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
    }

    setStore(accountId: string | null): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            Promise.all([this.loadPublisherGroups(accountId)])
                .then((values: [PublisherGroup[]]) => {
                    const splitRows: PublisherGroup[][] = this.postProcessLegacyServiceResponse(
                        values[0],
                        accountId
                    );

                    this.setState({
                        ...this.state,
                        accountId: accountId,
                        entities: splitRows[0],
                        systemEntities: splitRows[1],
                    });
                    resolve(true);
                })
                .catch(() => resolve(false));
        });
    }

    loadEntities(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.loadPublisherGroups(this.state.accountId).then(
                (publisherGroups: PublisherGroup[]) => {
                    const splitRows: PublisherGroup[][] = this.postProcessLegacyServiceResponse(
                        publisherGroups,
                        this.state.accountId
                    );

                    this.patchState(splitRows[0], 'entities');
                    this.patchState(splitRows[1], 'systemEntities');
                    resolve();
                },
                () => {
                    reject();
                }
            );
        });
    }

    setActiveEntity(entity: Partial<PublisherGroup>): void {
        const newActiveEntity = new PublisherGroupsLibraryStoreState()
            .activeEntity;

        this.setState({
            ...this.state,
            activeEntity: {
                ...newActiveEntity,
                entity: {
                    ...newActiveEntity.entity,
                    ...entity,
                },
            },
        });
    }

    saveActiveEntity(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.publisherGroupsService
                .upload(
                    this.state.activeEntity.entity,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        this.patchState(
                            new PublisherGroupsLibraryStoreState().activeEntity
                                .entity,
                            'activeEntity',
                            'entity'
                        );
                        resolve();
                    },
                    (error: HttpErrorResponse) => {
                        const fieldErrors = storeHelpers.getStoreFieldsErrorsState(
                            new PublisherGroupsLibraryStoreFieldsErrorsState(),
                            error
                        );
                        if (error.status === 413) {
                            fieldErrors.entries = ['File too large.'];
                        }
                        this.patchState(
                            fieldErrors,
                            'activeEntity',
                            'fieldErrors'
                        );
                        reject();
                    }
                );
        });
    }

    changeActiveEntity(event: ChangeEvent<PublisherGroup>): void {
        this.patchState(
            {...event.target, ...event.changes},
            'activeEntity',
            'entity'
        );
    }

    deleteEntity(publisherGroupId: string): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.publisherGroupsService
                .remove(publisherGroupId, this.requestStateUpdater)
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

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    private loadPublisherGroups(
        accountId: string | null
    ): Promise<PublisherGroup[]> {
        return new Promise<PublisherGroup[]>((resolve, reject) => {
            this.publisherGroupsService
                .list(accountId, this.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (publisherGroups: PublisherGroup[]) => {
                        resolve(publisherGroups);
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    /*This method is temporary and will be removed after the backend is updated. It simulates some aspects of the new service's responses:
     * - accountId is set on every publisherGroup
     * - the list of publisher groups is split into user and system publishers*/
    private postProcessLegacyServiceResponse(
        publisherGroups: PublisherGroup[],
        accountId: string
    ): PublisherGroup[][] {
        const splitRows: PublisherGroup[][] = [[], []];
        publisherGroups.forEach(pg => (pg.accountId = accountId));

        splitRows[0] = publisherGroups.filter(pg => pg.implicit === false);
        splitRows[1] = publisherGroups.filter(pg => pg.implicit === true);

        return splitRows;
    }
}
