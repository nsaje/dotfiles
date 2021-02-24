import './creative-candidate.component.less';

import {
    ChangeDetectionStrategy,
    Component,
    EventEmitter,
    HostBinding,
    Input,
    OnChanges,
    Output,
} from '@angular/core';
import {CreativeCandidate} from '../../../../../core/creatives/types/creative-candidate';
import {getTagColorCode} from '../../helpers/creatives-shared.helpers';
import {ChangeEvent} from '../../../../../shared/types/change-event';
import {CreativeCandidateFieldsErrorsState} from '../../types/creative-candidate-fields-errors-state';

@Component({
    selector: 'zem-creative-candidate',
    templateUrl: './creative-candidate.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreativeCandidateComponent implements OnChanges {
    @Input()
    candidate: CreativeCandidate;
    @Input()
    candidateErrors: CreativeCandidateFieldsErrorsState;
    @HostBinding('class.zem-creative-candidate--selected')
    @Input()
    isSelected: boolean;
    @Input()
    availableTags: string[];
    @Input()
    isLoadingTags: boolean = false;
    @Input()
    canUseExtraTrackers: boolean = false;
    @Output()
    remove: EventEmitter<void> = new EventEmitter<void>();
    @Output()
    candidateChange = new EventEmitter<ChangeEvent<CreativeCandidate>>();
    @Output()
    tagSearch: EventEmitter<string> = new EventEmitter<string>();

    coloredTags: {tag: string; color: number}[];

    ngOnChanges(): void {
        this.coloredTags = this.candidate.tags.map(tag => ({
            tag,
            color: getTagColorCode(tag),
        }));
    }

    removeButtonClicked($event: MouseEvent) {
        $event.stopPropagation();
        this.remove.emit();
    }
}
