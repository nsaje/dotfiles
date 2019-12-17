import './account-settings-drawer.view.less';

import {
    Component,
    Input,
    Inject,
    AfterViewInit,
    OnInit,
    OnDestroy,
} from '@angular/core';
import {
    ENTITY_MANAGER_CONFIG,
    ACCOUNT_TYPES,
    CURRENCIES,
} from '../../entity-manager.config';
import {AccountSettingsStore} from '../../services/account-settings-store/account-settings.store';
import {Subject, merge, Observable} from 'rxjs';
import * as messagesHelpers from '../../helpers/messages.helpers';
import {LevelStateParam, EntityType} from '../../../../app.constants';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {takeUntil, map, distinctUntilChanged, tap} from 'rxjs/operators';

@Component({
    selector: 'zem-account-settings-drawer',
    templateUrl: './account-settings-drawer.view.html',
    providers: [AccountSettingsStore],
})
export class AccountSettingsDrawerView
    implements OnInit, OnDestroy, AfterViewInit {
    @Input()
    entityId: string;
    @Input()
    newEntityParentId: string;

    EntityType = EntityType;
    ACCOUNT_TYPES = ACCOUNT_TYPES;
    CURRENCIES = CURRENCIES;

    isOpen: boolean;
    isNewEntity: boolean;
    isDefaultIconPreviewVisible: boolean;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: AccountSettingsStore,
        @Inject('zemPermissions') public zemPermissions: any,
        @Inject('ajs$state') private ajs$state: any,
        @Inject('ajs$location') private ajs$location: any
    ) {}

    ngOnInit(): void {
        this.isNewEntity = !this.entityId;

        this.subscribeToStateUpdates();
    }

    ngAfterViewInit() {
        if (this.isNewEntity) {
            this.store.loadEntityDefaults();
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
                .search({
                    [ENTITY_MANAGER_CONFIG.settingsQueryParam]: null,
                    [ENTITY_MANAGER_CONFIG.levelQueryParam]: null,
                    [ENTITY_MANAGER_CONFIG.idQueryParam]: null,
                })
                .replace();
        });
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

    toggleDefaultIconPreview() {
        this.isDefaultIconPreviewVisible = !this.isDefaultIconPreviewVisible;
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
            this.redirectToNewEntityAnalyticsView(this.store.state.entity.id);
        }
    }

    private redirectToNewEntityAnalyticsView(newEntityId: string) {
        this.redirectToEntityAnalyticsView(
            LevelStateParam.ACCOUNT,
            newEntityId
        );
    }

    private redirectToParentAnalyticsView(parentId: string) {
        this.redirectToEntityAnalyticsView(LevelStateParam.ACCOUNTS, parentId);
    }

    private redirectToEntityAnalyticsView(
        level: LevelStateParam,
        entityId: string
    ) {
        this.isOpen = false;
        const url = this.ajs$state.href('v2.analytics', {
            level: level,
            id: entityId,
        });
        this.ajs$location.url(url);
    }

    private subscribeToStateUpdates() {
        merge(this.createDefaultIconPreviewUpdater$())
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private createDefaultIconPreviewUpdater$(): Observable<string> {
        return this.store.state$.pipe(
            map(state => state.entity.defaultIconUrl),
            distinctUntilChanged(),
            tap(defaultIconUrl => {
                this.isDefaultIconPreviewVisible = commonHelpers.isDefined(
                    defaultIconUrl
                );
            })
        );
    }
}
