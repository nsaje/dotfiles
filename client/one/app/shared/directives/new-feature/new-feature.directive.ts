import './new-feature.directive.less';

import {
    Directive,
    ElementRef,
    Input,
    OnChanges,
    Renderer2,
} from '@angular/core';
import {isDefined} from '../../helpers/common.helpers';

@Directive({
    selector: '[zemNewFeature]',
})
export class NewFeatureDirective implements OnChanges {
    @Input()
    zemNewFeature: boolean = true;
    @Input()
    zemNewFeatureClass: string = '';

    private readonly CSS_CLASS: string = 'zem-new-feature';
    private readonly TEXT_CSS_CLASS: string = 'zem-new-feature__text';

    private readonly hostElement: HTMLElement;
    private newFeatureElement: HTMLElement;

    constructor(private elementRef: ElementRef, private renderer: Renderer2) {
        this.hostElement = this.elementRef.nativeElement;
    }

    ngOnChanges(): void {
        this.removeNewFeatureElement();

        if (this.zemNewFeature === true) {
            this.appendNewFeatureElement();
        }
    }

    private removeNewFeatureElement() {
        if (isDefined(this.newFeatureElement)) {
            this.renderer.removeChild(this.hostElement, this.newFeatureElement);
            this.newFeatureElement = null;
        }
    }

    private appendNewFeatureElement() {
        if (!isDefined(this.newFeatureElement)) {
            this.newFeatureElement = this.addHtmlElement(
                this.hostElement,
                'div',
                this.CSS_CLASS + ' ' + this.zemNewFeatureClass
            );
            this.addHtmlElement(
                this.newFeatureElement,
                'i',
                this.TEXT_CSS_CLASS,
                'NEW'
            );
        }
    }

    private addHtmlElement(
        parent: HTMLElement,
        type: string,
        cssClass: string,
        innerText?: string
    ): HTMLElement {
        const newElement: HTMLElement = this.renderer.createElement(type);
        newElement.className = cssClass;
        if (isDefined(innerText)) {
            newElement.innerText = innerText;
        }
        this.renderer.appendChild(parent, newElement);

        return newElement;
    }
}
