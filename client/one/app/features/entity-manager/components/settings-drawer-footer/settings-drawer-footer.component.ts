import './settings-drawer-footer.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    SimpleChanges,
    OnChanges,
} from '@angular/core';
import {EntityType} from '../../../../app.constants';
import * as messagesHelpers from '../../helpers/messages.helpers';

@Component({
    selector: 'zem-settings-drawer-footer',
    templateUrl: './settings-drawer-footer.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SettingsDrawerFooterComponent {
    @Input()
    isNewEntity: boolean;
    @Input()
    entityType: EntityType;
    @Input()
    userHasPermissionToArchive: boolean;
    @Input()
    isLoading: boolean;
    @Input()
    hasError: boolean;
    @Output()
    save = new EventEmitter<void>();
    @Output()
    cancel = new EventEmitter<void>();
    @Output()
    archive = new EventEmitter<void>();

    EntityType = EntityType;
}
