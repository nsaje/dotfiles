import './display-ad-preview.component.less';
import {
    Component,
    Input,
    ChangeDetectionStrategy,
    OnChanges,
    Inject,
    SimpleChanges,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import * as iframeHelpers from '../../helpers/iframe.helpers';
import {APP_CONFIG} from '../../../app.config';
import {AdType} from '../../../app.constants';
import {DOCUMENT} from '@angular/common';

@Component({
    selector: 'zem-display-ad-preview',
    templateUrl: './display-ad-preview.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DisplayAdPreviewComponent implements OnChanges {
    @Input()
    url: string;
    @Input()
    adType: AdType;
    @Input()
    displayHostedImageUrl: string;
    @Input()
    adTag: string;
    @Input()
    imageWidth: number;
    @Input()
    imageHeight: number;

    APP_CONFIG = APP_CONFIG;
    AdType = AdType;

    constructor(@Inject(DOCUMENT) private document: Document) {}

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.adTag) {
            setTimeout(() => {
                const iframe = this.document.getElementById(
                    'zem-display-ad-preview__iframe'
                );
                iframeHelpers.renderContentInIframe(iframe, this.adTag);
            });
        }
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemDisplayAdPreview',
    downgradeComponent({
        component: DisplayAdPreviewComponent,
        propagateDigest: false,
    })
);
