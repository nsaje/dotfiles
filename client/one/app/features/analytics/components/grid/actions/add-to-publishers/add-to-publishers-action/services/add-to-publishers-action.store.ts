import {Injectable, OnDestroy} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {Subject} from 'rxjs';
import {RequestStateUpdater} from '../../../../../../../../shared/types/request-state-updater';
import {takeUntil} from 'rxjs/operators';
import * as storeHelpers from '../../../../../../../../shared/helpers/store.helpers';
import * as commonHelpers from '../../../../../../../../shared/helpers/common.helpers';
import {AddToPublishersActionStoreState} from './add-to-publishers-action.store.state';
import {PublisherGroupsService} from '../../../../../../../../core/publisher-groups/services/publisher-groups.service';
import {PublisherGroup} from '../../../../../../../../core/publisher-groups/types/publisher-group';
import {PublisherInfo} from '../../../../../../../../core/publishers/types/publisher-info';
import {ChangeEvent} from '../../../../../../../../shared/types/change-event';
import {PublisherGroupsStoreState} from '../../../../../../../publisher-groups/services/publisher-groups-store/publisher-groups.store.state';
import {isDefined} from '../../../../../../../../shared/helpers/common.helpers';
import {HttpErrorResponse} from '@angular/common/http';
import {PublisherGroupFieldsErrorsState} from '../../../../../../../publisher-groups/types/publisher-group-fields-errors-state';

@Injectable()
export class AddToPublishersActionStore
    extends Store<AddToPublishersActionStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<undefined> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor(private publisherGroupsService: PublisherGroupsService) {
        super(new AddToPublishersActionStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    setActiveEntity(entity: Partial<PublisherGroup>): void {
        const newActiveEntity = new PublisherGroupsStoreState().activeEntity;

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

    changeActiveEntity(event: ChangeEvent<PublisherGroup>): void {
        this.patchState(
            {...event.target, ...event.changes},
            'activeEntity',
            'entity'
        );
    }

    setMode(mode: 'add' | 'create') {
        this.setState({
            ...new AddToPublishersActionStoreState(),
            mode,
        });
    }

    reset() {
        this.setState(new AddToPublishersActionStoreState());
    }

    search(accountId: string, keyword: string | null) {
        const isKeywordDefined = commonHelpers.isDefined(keyword);
        this.publisherGroupsService
            .listExplicit(
                null,
                accountId,
                !isKeywordDefined ? null : keyword.trim(),
                0,
                10,
                this.requestStateUpdater
            )
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe((publisherGroups: PublisherGroup[]) => {
                this.patchState(publisherGroups, 'availablePublisherGroups');
            });
    }

    save(accountId: string, publishers: PublisherInfo[]): Promise<void> {
        const publisherGroup: PublisherGroup = {
            ...this.state.activeEntity.entity,
            ...(!isDefined(this.state.activeEntity.entity.id) && {accountId}),
        };
        return new Promise<void>((resolve, reject) => {
            this.publisherGroupsService
                .addEntries(
                    publishers,
                    publisherGroup,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        resolve();
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new PublisherGroupFieldsErrorsState(),
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
}
