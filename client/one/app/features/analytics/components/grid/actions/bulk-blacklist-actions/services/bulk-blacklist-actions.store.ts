import {Injectable, OnDestroy} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {Subject} from 'rxjs';
import {RequestStateUpdater} from '../../../../../../../shared/types/request-state-updater';
import * as storeHelpers from '../../../../../../../shared/helpers/store.helpers';
import {
    PublisherBlacklistLevel,
    PublisherTargetingStatus,
} from '../../../../../../../app.constants';
import {takeUntil} from 'rxjs/operators';
import {HttpErrorResponse} from '@angular/common/http';
import {BulkBlacklistActionsStoreState} from './bulk-blacklist-actions.store.state';
import {PublishersService} from '../../../../../../../core/publishers/services/publishers.service';
import {PublisherInfo} from '../../../../../../../core/publishers/types/publisher-info';

@Injectable()
export class BulkBlacklistActionsStore
    extends Store<BulkBlacklistActionsStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<undefined> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor(private publishersService: PublishersService) {
        super(new BulkBlacklistActionsStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    updateBlacklistStatuses(
        selectedRows: PublisherInfo[],
        status: PublisherTargetingStatus,
        level: PublisherBlacklistLevel,
        entityId: number
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            this.publishersService
                .updateBlacklistStatuses(
                    selectedRows,
                    status,
                    level,
                    entityId,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        resolve(true);
                    },
                    (error: HttpErrorResponse) => {
                        resolve(false);
                    }
                );
        });
    }
}
