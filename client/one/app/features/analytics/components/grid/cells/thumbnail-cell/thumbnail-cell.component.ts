import './thumbnail-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {ICellRendererParams} from 'ag-grid-community';
import {
    GridRowDataStats,
    GridRowDataStatsValue,
} from '../../grid-bridge/types/grid-row-data';
import * as commonHelpers from '../../../../../../shared/helpers/common.helpers';
import {AdType} from '../../../../../../app.constants';
import {APP_OPTIONS} from '../../../../../../app.options';
import {GridRow} from '../../grid-bridge/types/grid-row';
import {
    DEFAULT_CREATIVE_HEIGHT,
    DEFAULT_CREATIVE_WIDTH,
} from './thumbnail-cell.component.constants';

@Component({
    templateUrl: './thumbnail-cell.component.html',
})
export class ThumbnailCellComponent implements ICellRendererAngularComp {
    stats: GridRowDataStats;

    url: string;
    displayUrl: string;
    breakdownName: string;
    brandName: string;
    description: string;
    callToAction: string;

    image: string;
    square: string;
    landscape: string;
    icon: string;
    adTag: string;

    adType: AdType;
    isNative: boolean;
    isImage: boolean;
    isAdTag: boolean;

    creativeWidth: number;
    creativeHeight: number;

    agInit(params: ICellRendererParams): void {
        this.stats = (params.data as GridRow).data.stats;

        this.url = commonHelpers.getValueOrDefault(
            (this.stats.urlLink as GridRowDataStatsValue)?.url as string,
            ''
        );
        this.displayUrl = commonHelpers.getValueOrDefault(
            (this.stats.display_url as GridRowDataStatsValue)?.value as string,
            ''
        );
        this.breakdownName = commonHelpers.getValueOrDefault(
            (this.stats.breakdown_name as GridRowDataStatsValue)
                ?.text as string,
            ''
        );
        this.brandName = commonHelpers.getValueOrDefault(
            (this.stats.brand_name as GridRowDataStatsValue)?.value as string,
            ''
        );
        this.description = commonHelpers.getValueOrDefault(
            (this.stats.description as GridRowDataStatsValue)?.value as string,
            ''
        );
        this.callToAction = commonHelpers.getValueOrDefault(
            (this.stats.call_to_action as GridRowDataStatsValue)
                ?.value as string,
            ''
        );

        this.image = (params.value as GridRowDataStatsValue).image;
        this.square = (params.value as GridRowDataStatsValue).square;
        this.landscape = (params.value as GridRowDataStatsValue).landscape;
        this.icon = (params.value as GridRowDataStatsValue).icon;
        this.adTag = (params.value as GridRowDataStatsValue).ad_tag;

        this.adType = this.getAdType(
            (this.stats.creative_type as GridRowDataStatsValue)?.value as string
        );
        this.isImage = this.adType === AdType.IMAGE;
        this.isAdTag = this.adType === AdType.AD_TAG;
        this.isNative = !this.isImage && !this.isAdTag;

        const creativeSize = this.parseCreativeSize(
            (this.stats.creative_size as GridRowDataStatsValue)?.value as string
        );
        this.creativeWidth = creativeSize[0];
        this.creativeHeight = creativeSize[1];
    }

    refresh(params: ICellRendererParams): boolean {
        const image = (params.value as GridRowDataStatsValue).image;
        const square = (params.value as GridRowDataStatsValue).square;
        const landscape = (params.value as GridRowDataStatsValue).landscape;
        const icon = (params.value as GridRowDataStatsValue).icon;
        const adTag = (params.value as GridRowDataStatsValue).ad_tag;

        if (
            this.image !== image ||
            this.square !== square ||
            this.landscape !== landscape ||
            this.icon !== icon ||
            this.adTag !== adTag
        ) {
            return false;
        }
        return true;
    }

    getAdType(name: string): AdType {
        if (commonHelpers.isDefined(name)) {
            return APP_OPTIONS.adTypes.find(item => item.name === name).value;
        }
        return null;
    }

    parseCreativeSize(creativeSize: string): number[] {
        if (commonHelpers.isDefined(creativeSize)) {
            return creativeSize
                .split('x')
                .map(item => parseInt(item.trim(), 10));
        }
        return [DEFAULT_CREATIVE_WIDTH, DEFAULT_CREATIVE_HEIGHT];
    }
}
