import {Directive, Input} from '@angular/core';
import {NgOptionHighlightDirective} from '@ng-select/ng-option-highlight';

@Directive({
    selector: '[zemTextHighlight]',
    exportAs: 'zemTextHighlight',
})
export class TextHighlightDirective extends NgOptionHighlightDirective {
    @Input('zemTextHighlight') term: string;
}
