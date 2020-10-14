import {Currency} from '../../../../../../app.constants';

export interface GridMetaData {
    ext?: GridMetaDataExt;
}

export interface GridMetaDataExt {
    currency?: Currency;
}
