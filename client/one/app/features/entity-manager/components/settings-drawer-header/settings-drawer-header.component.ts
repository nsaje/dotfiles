import './settings-drawer-header.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    SimpleChanges,
    OnChanges,
    Output,
    EventEmitter,
    OnInit,
} from '@angular/core';
import {EntityType} from '../../../../app.constants';
import * as entityHelpers from '../../helpers/entity.helpers';
import {SettingsDrawerHeaderMode} from './settings-drawer-header.constants';

@Component({
    selector: 'zem-settings-drawer-header',
    templateUrl: './settings-drawer-header.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SettingsDrawerHeaderComponent implements OnInit, OnChanges {
    @Input()
    entityId: string;
    @Input()
    entityType: EntityType;
    @Input()
    entityName: string;
    @Input()
    entityNamePlaceholder: string;
    @Input()
    showAdminLink: boolean;
    @Input()
    isAdminLinkAnInternalFeature: boolean;
    @Input()
    entityNameErrors: string[];
    @Input()
    isDisabled: boolean;
    @Output()
    entityNameChange = new EventEmitter<string>();

    EntityType = EntityType;
    SettingsDrawerHeaderMode = SettingsDrawerHeaderMode;

    entityNameModel: string;
    adminLink: string;
    mode: SettingsDrawerHeaderMode = SettingsDrawerHeaderMode.READ;

    ngOnInit(): void {
        if (!this.entityId) {
            this.switchToEditMode();
        }
    }

    ngOnChanges(changes: SimpleChanges) {
        if (changes.entityName) {
            this.entityNameModel = this.entityName;
        }
        if (changes.entityNameErrors && this.entityNameErrors.length > 0) {
            this.switchToEditMode();
        }
        if (changes.entityId) {
            this.adminLink = entityHelpers.getAdminLink(
                this.entityType,
                this.entityId
            );
        }
    }

    switchToReadMode() {
        this.mode = SettingsDrawerHeaderMode.READ;
    }

    switchToEditMode() {
        if (this.isDisabled) {
            return;
        }
        this.mode = SettingsDrawerHeaderMode.EDIT;
    }

    onEntityNameChange() {
        this.switchToReadMode();
        this.entityNameChange.emit(this.entityNameModel);
    }
}
