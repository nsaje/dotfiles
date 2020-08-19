export interface CheckboxSliderItem<T> {
    value: T;
    displayValue: string;
    selected: boolean | undefined;
    disabled?: boolean | undefined;
    hidden?: boolean | undefined;
}
