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
        const displayedOptions: CheckboxSliderItem<T>[] = this.options.filter(
            option => !option.hidden
        );
        const newSelection: CheckboxSliderItem<T>[] = [];
        if ($event) {
            newSelection.push(
                ...displayedOptions
                    .slice(0, optionIndex + 1)
                    .map(x => ({...x, selected: true}))
            );
            newSelection.push(...displayedOptions.slice(optionIndex + 1));
        } else {
            newSelection.push(...displayedOptions.slice(0, optionIndex));
            newSelection.push(
                ...displayedOptions
                    .slice(optionIndex)
                    .map(x => ({...x, selected: false}))
            );
        }

        this.selectionChange.emit(newSelection);
    }
}
