import './account-settings-drawer.view.less';

import {Component, Input, Inject, AfterViewInit} from '@angular/core';
import {ENTITY_MANAGER_CONFIG} from '../../entity-manager.config';

@Component({
    selector: 'zem-account-settings-drawer',
    templateUrl: './account-settings-drawer.view.html',
})
export class AccountSettingsDrawerView implements AfterViewInit {
    @Input()
    entityId: number;
    @Input()
    newEntityParentId: number;

    isOpen: boolean;
    isNewEntity: boolean;

    constructor(@Inject('ajs$location') private ajs$location: any) {}

    ngAfterViewInit() {
        this.isNewEntity = !this.entityId;

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
