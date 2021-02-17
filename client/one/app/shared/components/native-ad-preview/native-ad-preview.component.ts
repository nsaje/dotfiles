import './native-ad-preview.component.less';
import {Component, Input, ChangeDetectionStrategy, OnInit} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {APP_CONFIG} from '../../../app.config';
import * as commonHelpers from '../../helpers/common.helpers';
import {NativeAdPreviewConfig} from './types/native-ad-preview.config';
import {DEFAULT_NATIVE_AD_PREVIEW_CONFIG} from './native-ad-preview.config';

@Component({
    selector: 'zem-native-ad-preview',
    templateUrl: './native-ad-preview.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NativeAdPreviewComponent implements OnInit {
    @Input('nativeAdPreviewConfig')
    config: NativeAdPreviewConfig;
    @Input()
    url: string;
    @Input()
    landscapeHostedImageUrl: string;
    @Input()
    portraitHostedImageUrl: string;
    @Input()
    hostedImageUrl: string;
    @Input()
    title: string;
    @Input()
    brandName: string;
    @Input()
    description: string;
    @Input()
    displayUrl: string;
    @Input()
    hostedIconUrl: string;
    @Input()
    callToAction: string;
    @Input()
    showDesktopView: boolean = true;
    @Input()
    showMobileView: boolean = false;

    APP_CONFIG = APP_CONFIG;
    nativeAdPreviewConfig: NativeAdPreviewConfig;

    ngOnInit(): void {
        this.nativeAdPreviewConfig = {
            ...DEFAULT_NATIVE_AD_PREVIEW_CONFIG,
            ...commonHelpers.getValueOrDefault(this.config, {}),
        };
    }

    openUrl() {
        window.open(this.url, '_blank');
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemNativeAdPreview',
    downgradeComponent({
        component: NativeAdPreviewComponent,
        propagateDigest: false,
    })
);
