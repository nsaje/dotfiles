import {HttpParameterCodec} from '@angular/common/http';

export class ApiHttpParamEncoder implements HttpParameterCodec {
    encodeKey(k: string): string {
        return encodeURIComponent(k);
    }
    encodeValue(v: string): string {
        return encodeURIComponent(v);
    }
    decodeKey(k: string): string {
        return decodeURIComponent(k);
    }
    decodeValue(v: string) {
        return decodeURIComponent(v);
    }
}
