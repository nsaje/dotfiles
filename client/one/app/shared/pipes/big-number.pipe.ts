import {Pipe, PipeTransform} from '@angular/core';
/*
 * Display a big number in a readable way.
 * Usage:
 *   value | bigNumber
 * Example:
 *   {{ 2000000 | bigNumber }}
 *   formats to: 2M
 */
@Pipe({name: 'bigNumber'})
export class BigNumberPipe implements PipeTransform {
    transform(value: number): string {
        if (!value) {
            return '0';
        }

        const abs = Math.abs(value);
        if (abs >= Math.pow(10, 12)) {
            // tslint:disable-line
            return (value / Math.pow(10, 12)).toFixed() + ' T'; // tslint:disable-line
        } else if (abs < Math.pow(10, 12) && abs >= Math.pow(10, 9)) {
            // tslint:disable-line
            return (value / Math.pow(10, 9)).toFixed() + ' B'; // tslint:disable-line
        } else if (abs < Math.pow(10, 9) && abs >= Math.pow(10, 6)) {
            // tslint:disable-line
            return (value / Math.pow(10, 6)).toFixed() + ' M'; // tslint:disable-line
        } else if (abs < Math.pow(10, 6) && abs >= Math.pow(10, 3)) {
            // tslint:disable-line
            return (value / Math.pow(10, 3)).toFixed() + ' K'; // tslint:disable-line
        }
        return value.toString();
    }
}
