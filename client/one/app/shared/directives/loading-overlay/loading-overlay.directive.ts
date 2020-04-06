import './loading-overlay.directive.less';

import {
    Directive,
    ElementRef,
    Input,
    OnChanges,
    Renderer2,
} from '@angular/core';
import {isDefined} from '../../helpers/common.helpers';

@Directive({
    selector: '[zemLoadingOverlay]',
})
export class LoadingOverlayDirective implements OnChanges {
    @Input()
    zemLoadingOverlay: boolean;

    private readonly CSS_CLASS: string = 'zem-loading-overlay';
    private readonly LOADING_CSS_CLASS: string = 'zem-loading-overlay--loading';

    private readonly hostElement: HTMLElement;
    private loadingOverlayElement: HTMLElement;

    constructor(private elementRef: ElementRef, private renderer: Renderer2) {
        this.hostElement = this.elementRef.nativeElement;
    }

    ngOnChanges(): void {
        if (!isDefined(this.loadingOverlayElement)) {
            this.loadingOverlayElement = this.addHtmlElement(
                this.hostElement,
                'div',
                this.CSS_CLASS
            );
        }

        if (this.zemLoadingOverlay === true) {
            this.loadingOverlayElement.classList.add(this.LOADING_CSS_CLASS);
        } else {
            this.loadingOverlayElement.classList.remove(this.LOADING_CSS_CLASS);
        }
    }

    private addHtmlElement(
        parent: HTMLElement,
        type: string,
        cssClass: string
    ): HTMLElement {
        const newElement: HTMLElement = this.renderer.createElement(type);
        newElement.className = cssClass;
        this.renderer.appendChild(parent, newElement);

        return newElement;
    }
}
