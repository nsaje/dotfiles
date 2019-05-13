import './campaign-settings-drawer.view.less';

import {Component, Input, Inject, AfterViewInit, OnInit} from '@angular/core';
import {ENTITY_MANAGER_CONFIG} from '../../entity-manager.config';
import {CampaignSettingsStore} from '../../services/campaign-settings-store/campaign-settings.store';

@Component({
    selector: 'zem-campaign-settings-drawer',
    templateUrl: './campaign-settings-drawer.view.html',
    providers: [CampaignSettingsStore],
})
export class CampaignSettingsDrawerView implements OnInit, AfterViewInit {
    @Input()
    entityId: string;
    @Input()
    newEntityParentId: string;

    isOpen: boolean;
    isNewEntity: boolean;

    constructor(
        public store: CampaignSettingsStore,
        @Inject('ajs$location') private ajs$location: any
    ) {}

    ngOnInit() {
        this.isNewEntity = !this.entityId;
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

    open() {
        this.isOpen = true;
    }

    cancel() {
        this.isOpen = false;
        setTimeout(() => {
            this.ajs$location
                .search(ENTITY_MANAGER_CONFIG.settingsQueryParam, null)
                .replace();
        }, 250);
    }
}
