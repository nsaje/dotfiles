import {Unit, ValueModifierType} from '../rule-form.constants';

export interface ValueModifier {
    type?: ValueModifierType;
    value?: number;
    unit?: Unit;
}
