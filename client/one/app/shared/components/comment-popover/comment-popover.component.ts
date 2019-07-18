import './comment-popover.component.less';

import {Component, Input, ChangeDetectionStrategy} from '@angular/core';

@Component({
    selector: 'zem-comment-popover',
    templateUrl: './comment-popover.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CommentPopoverComponent {
    @Input()
    content: string;
    @Input()
    placement: string = 'top';
}
