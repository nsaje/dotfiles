import './ad-group-info.component.less';

import {
    Component,
    Input,
    OnInit,
    ChangeDetectionStrategy,
    OnChanges,
} from '@angular/core';
import {AdGroupInfoStep} from '../../bid-insights.constants';
import {
    ITEM_LENGTH_DISPLAY_LIMIT,
    STEP_TO_TITLE,
} from './ad-group-info.component.config';
import {AdGroupSectionInfo} from '../../types/ad-group-section-info';
import {FormattedAdGroupSectionInfo} from '../../types/formatted-ad-group-section-info';
import * as clone from 'clone';

@Component({
    selector: 'zem-ad-group-info',
    templateUrl: './ad-group-info.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdGroupInfoComponent implements OnInit, OnChanges {
    @Input()
    step: AdGroupInfoStep;
    @Input()
    adGroupInfo: AdGroupSectionInfo[];

    title: string;
    formattedAdGroupInfo: FormattedAdGroupSectionInfo[];
    showAll: boolean[];

    ngOnInit() {
        this.title = STEP_TO_TITLE[this.step];
        this.showAll = this.adGroupInfo.map(_ => {
            return false;
        });
    }

    ngOnChanges() {
        this.formattedAdGroupInfo = this.getFormattedAdGroupInfo(
            this.adGroupInfo
        );
    }

    handleShowAll(index: number) {
        const showAll = clone(this.showAll);
        showAll[index] = true;
        this.showAll = showAll;
    }

    private getFormattedAdGroupInfo(
        adGroupInfo: AdGroupSectionInfo[]
    ): FormattedAdGroupSectionInfo[] {
        return adGroupInfo.map(section => {
            let isTruncated = false;
            let itemsLength = 0;
            const truncatedItems: string[] = [];
            for (const item of section.items) {
                itemsLength = itemsLength + item.length;
                if (itemsLength < ITEM_LENGTH_DISPLAY_LIMIT) {
                    truncatedItems.push(item);
                } else {
                    isTruncated = true;
                    break;
                }
            }

            return {
                title: section.title,
                items: section.items.join(', '),
                truncatedItems: truncatedItems.join(', '),
                isTruncated: isTruncated,
            };
        });
    }
}
