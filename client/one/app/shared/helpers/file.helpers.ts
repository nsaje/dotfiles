import * as commonHelpers from './common.helpers';

export function encodeBase64(file: File): Promise<string> {
    return new Promise<string>(resolve => {
        if (!commonHelpers.isDefined(file)) {
            resolve(null);
            return;
        }
        const reader = new FileReader();
        reader.onloadend = () => {
            resolve(reader.result as string);
        };
        reader.onerror = () => {
            resolve(null);
        };
        reader.readAsDataURL(file);
    });
}
