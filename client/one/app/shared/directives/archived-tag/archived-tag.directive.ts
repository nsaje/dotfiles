import './archived-tag.directive.less';

import {
    Directive,
    ElementRef,
    Input,
    OnChanges,
    Renderer2,
} from '@angular/core';
import {TagDirective} from '../tag/tag.directive';

@Directive({
    selector: '[zemArchivedTag]',
})
export class ArchivedTagDirective extends TagDirective implements OnChanges {
    @Input()
    zemArchivedTag: boolean = true;
    @Input()
    zemArchivedTagClass: string = '';

    constructor(
        protected elementRef: ElementRef,
        protected renderer: Renderer2
    ) {
        super(elementRef, renderer);
        this.tagText = 'ARCHIVED';
    }

    ngOnChanges(): void {
        this.isTagDisplayed = this.zemArchivedTag;
        this.tagClass = 'zem-archived-tag ' + this.zemArchivedTagClass;
        super.updateDisplay();
    }
}
