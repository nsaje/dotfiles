import './tag.directive.less';

import {ElementRef, OnChanges, Renderer2, Directive} from '@angular/core';
import {isDefined} from '../../helpers/common.helpers';

@Directive()
export abstract class TagDirective implements OnChanges {
    isTagDisplayed: boolean = true;
    tagClass: string = '';
    tagText: string = '';
    tagTextClass: string = '';

    private readonly CSS_CLASS: string = 'zem-tag';
    private readonly TEXT_CSS_CLASS: string = 'zem-tag__text';

    private readonly hostElement: HTMLElement;
    private tagElement: HTMLElement;

    constructor(
        protected elementRef: ElementRef,
        protected renderer: Renderer2
    ) {
        this.hostElement = this.elementRef.nativeElement;
    }

    abstract ngOnChanges(): void;

    updateDisplay(): void {
        this.removeTagElement();

        if (this.isTagDisplayed === true) {
            this.appendTagElement();
        }
    }

    private removeTagElement() {
        if (isDefined(this.tagElement)) {
            this.renderer.removeChild(this.hostElement, this.tagElement);
            this.tagElement = null;
        }
    }

    private appendTagElement() {
        if (!isDefined(this.tagElement)) {
            this.tagElement = this.addHtmlElement(
                this.hostElement,
                'div',
                this.CSS_CLASS + ' ' + this.tagClass
            );
            this.addHtmlElement(
                this.tagElement,
                'i',
                this.TEXT_CSS_CLASS + ' ' + this.tagTextClass,
                this.tagText
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
