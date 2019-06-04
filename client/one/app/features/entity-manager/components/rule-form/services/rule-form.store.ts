import {RuleFormStoreState} from './rule-form.store.state';
import {Store} from 'rxjs-observable-store';
import {RuleDimension, TimeRange} from '../rule-form.constants';
import {RuleAction} from '../types/rule-action';
import {RuleNotification} from '../types/rule-notification';
import {RuleCondition} from '../types/rule-condition';

export class RuleFormStore extends Store<RuleFormStoreState> {
    constructor() {
        super(new RuleFormStoreState());
    }

    setDimension(dimension: RuleDimension) {
        this.updateState(dimension, 'rule', 'dimension');
    }

    setName(name: string) {
        this.updateState(name, 'rule', 'name');
    }

    setAction(action: RuleAction) {
        this.updateState(action, 'rule', 'action');
    }

    setNotification(notification: RuleNotification) {
        this.updateState(notification, 'rule', 'notification');
    }

    setConditions(conditions: RuleCondition[]) {
        this.updateState(conditions, 'rule', 'conditions');
    }

    setTimeRange(timeRange: TimeRange) {
        this.updateState(timeRange, 'rule', 'timeRange');
    }
}
