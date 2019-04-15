import './settings-drawer-header.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    SimpleChanges,
    OnChanges,
} from '@angular/core';
import {EntityType} from '../../../../app.constants';
import * as entityHelpers from '../../helpers/entity.helpers';

@Component({
    selector: 'zem-settings-drawer-header',
    templateUrl: './settings-drawer-header.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SettingsDrawerHeaderComponent implements OnChanges {
    @Input()
    entityId: string;
    @Input()
    entityType: EntityType;
    @Input()
    entityName: string;
    @Input()
    showAdminLink: boolean;
    @Input()
    isAdminLinkAnInternalFeature: boolean;

    EntityType = EntityType;

    adminLink: string;

    ngOnChanges(changes: SimpleChanges) {
        if (changes.entityId) {
            this.adminLink = entityHelpers.getAdminLink(
                EntityType.AD_GROUP,
                this.entityId
            );
        }
    }
}
