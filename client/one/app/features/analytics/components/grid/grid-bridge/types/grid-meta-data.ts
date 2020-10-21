import {Breakdown, Currency, Level} from '../../../../../../app.constants';

export interface GridMetaData {
    ext?: GridMetaDataExt;
    level?: Level;
    breakdown?: Breakdown;
}

export interface GridMetaDataExt {
    currency?: Currency;
}
