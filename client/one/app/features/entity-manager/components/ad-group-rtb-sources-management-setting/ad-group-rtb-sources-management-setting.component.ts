import './ad-group-rtb-sources-management-setting.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Output,
    Input,
} from '@angular/core';

@Component({
    selector: 'zem-ad-group-rtb-sources-management-setting',
    templateUrl: './ad-group-rtb-sources-management-setting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdGroupRTBSourcesManagementSettingComponent {
    @Input()
    manageRtbSourcesAsOne: boolean;
    @Input()
    isDisabled: boolean;
    @Input()
    agencyUsesRealtimeAutopilot: boolean;
    @Output()
    manageRtbSourcesAsOneChange = new EventEmitter<boolean>();
}
