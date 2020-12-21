import {Directive, Input, TemplateRef} from '@angular/core';

@Directive({selector: '[zemMultiStepStep]'})
export class MultiStepStepDirective {
    @Input('zemMultiStepStep') stepId: number;
    constructor(public content: TemplateRef<any>) {}
}
