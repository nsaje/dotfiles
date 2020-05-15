import {Currency} from '../../../app.constants';

export interface CreditTotal {
    total: string;
    allocated: string;
    past: string;
    available: string;
    currency: Currency;
}
