import './thumbnail-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {
    DEFAULT_CREATIVE_HEIGHT,
    DEFAULT_CREATIVE_WIDTH,
} from './thumbnail-cell.component.constants';
import {AdType} from '../../../app.constants';
import {ThumbnailCellRendererParams} from './types/thumbnail-cell-renderer-params';
import {ThumbnailData} from './types/thumbnail-data';

@Component({
    templateUrl: './thumbnail-cell.component.html',
})
export class ThumbnailCellComponent implements ICellRendererAngularComp {
    readonly DEFAULT_CREATIVE_WIDTH: number = DEFAULT_CREATIVE_WIDTH;
    readonly DEFAULT_CREATIVE_HEIGHT: number = DEFAULT_CREATIVE_HEIGHT;

    thumbnail: ThumbnailData;
    isNative: boolean;

    agInit(params: ThumbnailCellRendererParams): void {
        this.thumbnail = params.value;
        this.isNative = ![AdType.IMAGE, AdType.AD_TAG].includes(
            params.data.type
        );
    }

    refresh(params: ThumbnailCellRendererParams): boolean {
        const propsToCompare: (keyof ThumbnailData)[] = [
            'displayHostedImageUrl',
            'hostedImageUrl',
            'landscapeHostedImageUrl',
            'hostedIconUrl',
            'adTag',
        ];

        return !propsToCompare.some(prop =>
            this.propHasDifferentValue(this.thumbnail, params.data, prop)
        );
    }

    private propHasDifferentValue<T>(obj1: T, obj2: T, prop: keyof T): boolean {
        return obj1[prop] !== obj2[prop];
    }
}
