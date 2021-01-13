import {AdType} from '../../../../app.constants';

export interface CreativesSearchParams {
    keyword: string | null;
    creativeType: AdType | null;
    tags: string[] | null;
}
