import './internal-feature.directive.less';

import {
    Directive,
    ElementRef,
    Input,
    OnChanges,
    SimpleChanges,
    OnInit,
    Renderer2,
} from '@angular/core';
import * as commonHelpers from '../../helpers/common.helpers';

@Directive({
    selector: '[zemInternalFeature]',
})
export class InternalFeatureDirective implements OnInit, OnChanges {
    @Input('zemInternalFeature')
    isInternal: boolean = true;

    private hostElement: HTMLElement;
    private internalFeatureIndicatorElement: HTMLElement;
    private hostElementClassName: string;
    private internalFeatureIndicatorClassName: string;

    constructor(private elementRef: ElementRef, private renderer: Renderer2) {
        this.hostElementClassName = 'zem-internal-feature';
        this.internalFeatureIndicatorClassName =
            'zem-internal-feature__indicator';
        this.hostElement = this.elementRef.nativeElement;
    }

    ngOnInit(): void {
        this.handleIsInternalInputChange(this.isInternal);
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.zemInternalFeature) {
            this.handleIsInternalInputChange(this.isInternal);
        }
    }

    private handleIsInternalInputChange(isInternal: boolean): void {
        if (
            !commonHelpers.isDefined(isInternal) ||
            isInternal.toString() === '' ||
            isInternal.toString() === 'true'
        ) {
            this.appendInternalFeatureElement();
        } else {
            this.removeInternalFeatureElement();
        }
    }

    private appendInternalFeatureElement() {
        this.renderer.addClass(this.hostElement, this.hostElementClassName);

        this.internalFeatureIndicatorElement = this.renderer.createElement('i');
        this.internalFeatureIndicatorElement.className = this.internalFeatureIndicatorClassName;
        this.renderer.appendChild(
            this.hostElement,
            this.internalFeatureIndicatorElement
        );
    }

    private removeInternalFeatureElement() {
        this.renderer.removeClass(this.hostElement, this.hostElementClassName);

        if (this.internalFeatureIndicatorElement) {
            this.renderer.removeChild(
                this.hostElement,
                this.internalFeatureIndicatorElement
            );
            this.internalFeatureIndicatorElement = null;
        }
    }
}
