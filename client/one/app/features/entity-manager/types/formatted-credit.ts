import {Credit} from '../../../core/credits/types/credit';
import {Omit} from '../../../shared/types/omit';

export interface FormattedCredit
    extends Omit<Credit, 'createdOn' | 'startDate' | 'endDate'> {
    createdOn: string;
    startDate: string;
    endDate: string;
}
