import './submission-status-item.component.less';

import {
    ChangeDetectionStrategy,
    Component,
    Input,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {ContentAdApprovalStatus} from '../../../../../../../../app.constants';
import {APP_CONFIG} from '../../../../../../../../app.config';
import * as commonHelpers from '../../../../../../../../shared/helpers/common.helpers';

@Component({
    selector: 'zem-submission-status-item',
    templateUrl: './submission-status-item.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SubmissionStatusItemComponent implements OnChanges {
    @Input()
    name: string;
    @Input()
    status: ContentAdApprovalStatus;
    @Input()
    sourceState: string;
    @Input()
    text: string;
    @Input()
    isTextStrong: boolean;
    @Input()
    sourceLink: string;
    @Input()
    isSourceLinkVisible: boolean;
    @Input()
    isSourceLinkAnInternalFeature: boolean;

    fullName: string = '';
    iconUrl: string = `${APP_CONFIG.staticUrl}/one/images/link.svg`;

    ngOnChanges(changes: SimpleChanges): void {
        this.fullName = this.getFullName(this.name, this.sourceState);
    }

    private getFullName(name: string, sourceState: string): string {
        if (commonHelpers.isNotEmpty(sourceState)) {
            return `${name} ${sourceState}:`;
        }
        return `${name}:`;
    }
}
