import './bulk-blacklist-actions.component.less';

import {
    ChangeDetectionStrategy,
    Component,
    EventEmitter,
    Inject,
    Input,
    OnChanges,
    OnInit,
    Output,
    SimpleChanges,
    ViewChildren,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {
    Level,
    PublisherBlacklistLevel,
    PublisherTargetingStatus,
} from '../../../../../../app.constants';
import {BulkBlacklistActionsStore} from './services/bulk-blacklist-actions.store';
import {PublisherBlacklistActionLevel} from '../../../../../../core/publishers/types/publisher-blacklist-action-level';
import {PublisherBlacklistAction} from '../../../../../../core/publishers/types/publisher-blacklist-action';
import {DropdownDirective} from '../../../../../../shared/components/dropdown/dropdown.directive';
import {isEmpty} from '../../../../../../shared/helpers/array.helpers';
import {PublisherInfo} from '../../../../../../core/publishers/types/publisher-info';
import {PublishersService} from '../../../../../../core/publishers/services/publishers.service';

@Component({
    selector: 'zem-bulk-blacklist-actions',
    templateUrl: './bulk-blacklist-actions.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [BulkBlacklistActionsStore],
})
export class BulkBlacklistActionsComponent implements OnInit, OnChanges {
    @ViewChildren(DropdownDirective)
    dropdowns: DropdownDirective[];

    @Input()
    selectedRows: PublisherInfo[];
    @Input()
    level: Level;
    @Input()
    accountId: number;
    @Input()
    campaignId: number;
    @Input()
    adGroupId: number;
    @Output()
    actionSuccess: EventEmitter<boolean> = new EventEmitter<boolean>();

    dropdownsDisabled: boolean = false;
    blacklistActions: PublisherBlacklistAction[] = [];
    blacklistLevels: PublisherBlacklistActionLevel[] = [];

    constructor(
        public store: BulkBlacklistActionsStore,
        public service: PublishersService,
        @Inject('zemPermissions') public zemPermissions: any
    ) {}

    ngOnInit() {
        this.blacklistActions = this.service.getBlacklistActions();
        this.blacklistLevels = this.service.getBlacklistLevels(
            this.accountId,
            this.campaignId,
            this.adGroupId
        );
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.selectedRows) {
            this.dropdownsDisabled = isEmpty(this.selectedRows);
        }
        if (changes.adGroupId || changes.campaignId || changes.accountId) {
            this.blacklistLevels = this.service.getBlacklistLevels(
                this.accountId,
                this.campaignId,
                this.adGroupId
            );
        }
    }

    updateBlacklistStatuses(
        status: PublisherTargetingStatus,
        level: PublisherBlacklistLevel
    ) {
        this.dropdowns.forEach(dropdown => dropdown.close());

        if (level === PublisherBlacklistLevel.GLOBAL) {
            if (
                !confirm(
                    'This action will affect all accounts. Are you sure you want to proceed?'
                )
            ) {
                return;
            }
        }

        const entityId: number = this.getEntityIdForLevel(level);
        this.store
            .updateBlacklistStatuses(this.selectedRows, status, level, entityId)
            .then((success: boolean) => {
                this.actionSuccess.emit(success);
            });
    }

    private getEntityIdForLevel(
        level: PublisherBlacklistLevel
    ): number | undefined {
        switch (level) {
            case PublisherBlacklistLevel.ACCOUNT:
                return this.accountId;
            case PublisherBlacklistLevel.CAMPAIGN:
                return this.campaignId;
            case PublisherBlacklistLevel.ADGROUP:
                return this.adGroupId;
        }
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemBulkBlacklistActions',
    downgradeComponent({
        component: BulkBlacklistActionsComponent,
        propagateDigest: false,
    })
);
