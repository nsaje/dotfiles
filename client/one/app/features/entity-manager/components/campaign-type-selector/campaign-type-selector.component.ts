import './campaign-type-selector.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Output,
    EventEmitter,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {CAMPAIGN_TYPE} from '../../../../app.constants';

@Component({
    selector: 'zem-campaign-type-selector',
    templateUrl: './campaign-type-selector.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CampaignTypeSelectorComponent {
    @Output()
    onSelect = new EventEmitter<number>();

    CAMPAIGN_TYPE = CAMPAIGN_TYPE;
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemCampaignTypeSelector',
    downgradeComponent({
        component: CampaignTypeSelectorComponent,
        outputs: ['onSelect'],
    })
);
