import './campaign-creator-modal.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Output,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';

@Component({
    selector: 'zem-campaign-creator-modal',
    templateUrl: './campaign-creator-modal.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CampaignCreatorModalComponent {
    @Output()
    onClose = new EventEmitter<number>();
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemCampaignCreatorModal',
    downgradeComponent({
        component: CampaignCreatorModalComponent,
        outputs: ['onClose'],
    })
);
