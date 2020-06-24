import './checkbox-slider.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    EventEmitter,
    Output,
} from '@angular/core';
import {CheckboxSliderItem} from './types/checkbox-slider-item';

@Component({
    selector: 'zem-checkbox-slider',
    templateUrl: './checkbox-slider.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CheckboxSliderComponent<T> {
    @Input()
    options: CheckboxSliderItem<T>[];
    @Input()
    isDisabled: boolean = false;
    @Input()
    errors: string[];

    @Output()
    selectionChange: EventEmitter<CheckboxSliderItem<T>[]> = new EventEmitter<
        CheckboxSliderItem<T>[]
    >();

    trackByIndex(index: number): string {
        return index.toString();
    }

    toggle($event: boolean, optionIndex: number) {
        const changes: CheckboxSliderItem<T>[] = [];
        if ($event) {
            changes.push(
                ...this.options
                    .slice(0, optionIndex + 1)
                    .map(x => ({...x, selected: true}))
            );
            changes.push(...this.options.slice(optionIndex + 1));
        } else {
            changes.push(...this.options.slice(0, optionIndex));
            changes.push(
                ...this.options
                    .slice(optionIndex)
                    .map(x => ({...x, selected: false}))
            );
        }

        this.selectionChange.emit(changes);
    }
}
