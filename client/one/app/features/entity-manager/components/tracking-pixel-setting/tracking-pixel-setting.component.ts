import './tracking-pixel-setting.component.less';

import {Component, ChangeDetectionStrategy, Input} from '@angular/core';

@Component({
    selector: 'zem-tracking-pixel-setting',
    templateUrl: './tracking-pixel-setting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TrackingPixelSettingComponent {
    @Input()
    pixelUrls: string[];
    @Input()
    redirectJavaScript: string;
}
