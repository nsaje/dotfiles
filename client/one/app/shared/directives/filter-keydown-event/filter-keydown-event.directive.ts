import {
    Directive,
    HostListener,
    Output,
    EventEmitter,
    Input,
} from '@angular/core';
import {KeyCode} from '../../../app.constants';
import * as commonHelpers from '../../helpers/common.helpers';

@Directive({
    selector: '[zemFilterKeydownEvent]',
})
export class FilterKeydownEventDirective {
    @Input()
    keyFilter: number[];
    @Output()
    filteredKeydown = new EventEmitter<KeyboardEvent>();
    @Input()
    filterDeletionKeys: boolean = true;

    @HostListener('keydown', ['$event'])
    handle($event: KeyboardEvent) {
        const filter = this.createFilter();
        if (
            filter.indexOf($event.keyCode) !== -1 ||
            $event.ctrlKey === true ||
            $event.metaKey === true
        ) {
            return;
        }

        this.filteredKeydown.emit($event);
    }

    private createFilter(): number[] {
        const filter: number[] = [
            KeyCode.TAB,
            KeyCode.SHIFT,
            KeyCode.ESCAPE,
            KeyCode.END,
            KeyCode.HOME,
            KeyCode.LEFT_ARROW,
            KeyCode.UP_ARROW,
            KeyCode.RIGHT_ARROW,
            KeyCode.DOWN_ARROW,
        ];
        const deletionKeys: number[] = [KeyCode.BACKSPACE, KeyCode.DELETE];

        let selectedFilters: number[] = filter.concat(
            commonHelpers.getValueOrDefault(this.keyFilter, [])
        );

        if (this.filterDeletionKeys) {
            selectedFilters = selectedFilters.concat(deletionKeys);
        }

        return selectedFilters;
    }
}
