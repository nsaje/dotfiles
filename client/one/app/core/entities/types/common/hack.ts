import {HackLevel} from '../../../../app.constants';

export interface Hack {
    summary: string;
    source: string;
    level: HackLevel;
    details: string;
    confirmed: boolean;
}
