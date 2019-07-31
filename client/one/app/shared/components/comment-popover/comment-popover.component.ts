import './comment-popover.component.less';

import {
    Component,
    Input,
    ChangeDetectionStrategy,
    TemplateRef,
} from '@angular/core';

@Component({
    selector: 'zem-comment-popover',
    templateUrl: './comment-popover.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CommentPopoverComponent {
    @Input()
    content: string | TemplateRef<any>;
    @Input()
    stayOpenOnHover: boolean = false;
    @Input()
    placement: string = 'top';
}
