import {FilterKeydownEventDirective} from './filter-keydown-event.directive';
import {KeyCode} from '../../app.constants';

describe('FilterKeydownEventDirective', () => {
    let directive: FilterKeydownEventDirective;

    beforeEach(() => {
        directive = new FilterKeydownEventDirective();
        directive.keyFilter = [KeyCode.ENTER, KeyCode.SPACE];

        spyOn(directive.filteredKeydown, 'emit').and.stub();
    });

    it('should emit filteredKeydown event', () => {
        const digit5 = 53;
        const $event: any = {keyCode: digit5};
        directive.handle($event);
        expect(directive.filteredKeydown.emit).toHaveBeenCalled();
        (<any>directive.filteredKeydown.emit).calls.reset();

        const keyA = 65;
        $event.keyCode = keyA;
        directive.handle($event);
        expect(directive.filteredKeydown.emit).toHaveBeenCalled();
        (<any>directive.filteredKeydown.emit).calls.reset();

        const period = 190;
        $event.keyCode = period;
        directive.handle($event);
        expect(directive.filteredKeydown.emit).toHaveBeenCalled();
        (<any>directive.filteredKeydown.emit).calls.reset();

        const comma = 188;
        $event.keyCode = comma;
        directive.handle($event);
        expect(directive.filteredKeydown.emit).toHaveBeenCalled();
    });

    it('should not emit filteredKeydown event', () => {
        const $event: any = {keyCode: KeyCode.ENTER};
        directive.handle($event);
        expect(directive.filteredKeydown.emit).not.toHaveBeenCalled();

        $event.keyCode = KeyCode.SPACE;
        directive.handle($event);
        expect(directive.filteredKeydown.emit).not.toHaveBeenCalled();

        $event.keyCode = KeyCode.BACKSPACE;
        directive.handle($event);
        expect(directive.filteredKeydown.emit).not.toHaveBeenCalled();
    });
});
