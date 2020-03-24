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

    setStore(accountId: string | null): void {
        this.setState({
            ...this.state,
            accountId: accountId,
        });
    }

    loadEntities(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.loadPublisherGroups(this.state.accountId).then(
                (publisherGroups: PublisherGroup[]) => {
                    publisherGroups.forEach(
                        pg => (pg.accountId = this.state.accountId) // TODO: remove this after backend is updated
                    );
                    this.patchState(
                        publisherGroups.filter(pg => pg.implicit === false),
                        'entities'
                    );
                    this.patchState(
                        publisherGroups.filter(pg => pg.implicit === true),
                        'systemEntities'
                    );
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
}
