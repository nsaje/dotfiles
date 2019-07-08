import './campaign-settings-drawer.view.less';

import {
    Component,
    Input,
    Inject,
    AfterViewInit,
    OnInit,
    OnDestroy,
} from '@angular/core';
import {ENTITY_MANAGER_CONFIG} from '../../entity-manager.config';
import {CampaignSettingsStore} from '../../services/campaign-settings-store/campaign-settings.store';
import {
    LevelStateParam,
    EntityType,
    CampaignType,
} from '../../../../app.constants';
import * as messagesHelpers from '../../helpers/messages.helpers';
import {Subject, Observable, merge} from 'rxjs';
import {takeUntil, distinctUntilChanged, map, tap} from 'rxjs/operators';

@Component({
    selector: 'zem-campaign-settings-drawer',
    templateUrl: './campaign-settings-drawer.view.html',
    providers: [CampaignSettingsStore],
})
export class CampaignSettingsDrawerView
    implements OnInit, OnDestroy, AfterViewInit {
    @Input()
    entityId: string;
    @Input()
    newEntityParentId: string;

    EntityType = EntityType;

    isOpen: boolean;
    isNewEntity: boolean;
    campaignType: CampaignType;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: CampaignSettingsStore,
        @Inject('zemPermissions') public zemPermissions: any,
        @Inject('ajs$state') private ajs$state: any,
        @Inject('ajs$location') private ajs$location: any
    ) {}

    ngOnInit() {
        this.isNewEntity = !this.entityId;

        this.subscribeToStateUpdates();
    }

    ngAfterViewInit() {
        if (this.isNewEntity) {
            this.store.loadEntityDefaults(this.newEntityParentId);
        } else {
            this.store.loadEntity(this.entityId);
        }

        setTimeout(() => {
            this.open();
        });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    open() {
        this.isOpen = true;
    }

    close() {
        this.isOpen = false;
        setTimeout(() => {
            this.ajs$location
                .search(ENTITY_MANAGER_CONFIG.settingsQueryParam, null)
                .replace();
        }, 250);
    }

    cancel() {
        let shouldCloseDrawer = true;
        if (this.store.doEntitySettingsHaveUnsavedChanges()) {
            shouldCloseDrawer = confirm(
                messagesHelpers.getClosingUnsavedChangesConfirmMessage()
            );
        }
        if (shouldCloseDrawer) {
            if (this.isNewEntity) {
                this.redirectToParentAnalyticsView(this.newEntityParentId);
            } else {
                this.close();
            }
        }
    }

    async saveSettings() {
        const shouldCloseDrawer = await this.store.saveEntity();
        if (shouldCloseDrawer) {
            if (this.isNewEntity) {
                this.redirectToNewEntityAnalyticsView(
                    this.store.state.entity.id
                );
            } else {
                this.close();
            }
        }
    }

    async archive() {
        const shouldReload = await this.store.archiveEntity();
        if (shouldReload) {
            location.reload();
        }
    }

    private subscribeToStateUpdates() {
        merge(this.createCampaignTypeUpdater$())
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private createCampaignTypeUpdater$(): Observable<string> {
        return this.store.state$.pipe(
            map(state => state.entity.type),
            distinctUntilChanged(),
            tap(type => {
                this.campaignType = CampaignType[type];
            })
        );
    }

    private redirectToNewEntityAnalyticsView(newEntityId: string) {
        this.redirectToEntityAnalyticsView(
            LevelStateParam.CAMPAIGN,
            newEntityId
        );
    }

    private redirectToParentAnalyticsView(parentId: string) {
        this.redirectToEntityAnalyticsView(LevelStateParam.ACCOUNT, parentId);
    }

    private redirectToEntityAnalyticsView(
        level: LevelStateParam,
        entityId: string
    ) {
        const url = this.ajs$state.href('v2.analytics', {
            level: level,
            id: entityId,
        });
        this.ajs$location.url(url);
    }
}
