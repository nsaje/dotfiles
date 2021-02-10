import {Directive, Input, TemplateRef} from '@angular/core';

@Directive({selector: '[zemTab]'})
export class TabDirective {
    @Input('zemTab') tabName: string;
    constructor(public content: TemplateRef<any>) {}
}
