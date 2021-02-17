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

@Component({
    selector: 'zem-creative-candidate',
    templateUrl: './creative-candidate.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreativeCandidateComponent implements OnChanges {
    @Input()
    candidate: CreativeCandidate;
    @HostBinding('class.zem-creative-candidate--selected')
    @Input()
    isSelected: boolean;
    @Output()
    remove: EventEmitter<void> = new EventEmitter<void>();

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
