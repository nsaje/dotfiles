import './new-feature.directive.less';

import {
    Directive,
    ElementRef,
    Input,
    OnChanges,
    Renderer2,
} from '@angular/core';
import {TagDirectiveBase} from '../tag-directive-base/tag-directive-base';

@Directive({
    selector: '[zemNewFeature]',
})
export class NewFeatureDirective extends TagDirectiveBase implements OnChanges {
    @Input()
    zemNewFeature: boolean = true;
    @Input()
    zemNewFeatureClass: string = '';

    constructor(
        protected elementRef: ElementRef,
        protected renderer: Renderer2
    ) {
        super(elementRef, renderer);
        this.tagText = 'NEW';
    }

    ngOnChanges(): void {
        this.isTagDisplayed = this.zemNewFeature;
        this.tagClass = 'zem-new-feature ' + this.zemNewFeatureClass;
        super.updateDisplay();
    }
}
