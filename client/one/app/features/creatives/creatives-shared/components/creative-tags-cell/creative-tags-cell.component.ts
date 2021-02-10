import './creative-tags-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {CreativeRendererParams} from '../../types/creative.renderer-params';
import {getTagColorCode} from '../../helpers/creatives-shared.helpers';

@Component({
    templateUrl: './creative-tags-cell.component.html',
})
export class CreativeTagsCellComponent implements ICellRendererAngularComp {
    coloredTags: {tag: string; color: number}[];

    agInit(params: CreativeRendererParams) {
        this.coloredTags = params.data.tags.map(tag => ({
            tag,
            color: getTagColorCode(tag),
        }));
    }

    refresh(): boolean {
        return false;
    }
}
