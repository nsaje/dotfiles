import './campaign-creator.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Output,
    EventEmitter,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';

@Component({
    selector: 'zem-campaign-creator',
    templateUrl: './campaign-creator.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CampaignCreatorComponent {
    @Output()
    onSubmit = new EventEmitter<number>();
}
