import {ElementRef, Renderer2} from '@angular/core';
import {ArchivedTagDirective} from './archived-tag.directive';

describe('ArchivedTagDirective', () => {
    let elementRefStub: ElementRef;
    let rendererSpy: jasmine.SpyObj<Renderer2>;
    let directive: ArchivedTagDirective;

    beforeEach(() => {
        elementRefStub = {nativeElement: jasmine.any(Object)};
        rendererSpy = jasmine.createSpyObj('Renderer2', [
            'createElement',
            'appendChild',
            'removeChild',
        ]);
        rendererSpy.createElement.and.returnValue({});
        directive = new ArchivedTagDirective(elementRefStub, rendererSpy);
    });

    it('should supply inputs to super class on changes', () => {
        expect(directive.isTagDisplayed).toBeTrue();
        expect(directive.tagClass).toEqual('');

        directive.zemArchivedTag = false;
        directive.zemArchivedTagClass = 'xxx';
        directive.ngOnChanges();
        expect(directive.isTagDisplayed).toBeFalse();
        expect(directive.tagClass.split(' ').includes('xxx')).toBeTrue();

        directive.zemArchivedTag = true;
        directive.zemArchivedTagClass = 'test';
        directive.ngOnChanges();
        expect(directive.isTagDisplayed).toBeTrue();
        expect(directive.tagClass.split(' ').includes('test')).toBeTrue();
    });
});
