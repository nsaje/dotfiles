import {simulateTextChange} from './text-input.helpers';

describe('textInputHelpers', () => {
    function createKeyboardEvent(
        key: string,
        selectionStart: number,
        selectionEnd: number
    ): KeyboardEvent {
        const keyboardEvent: any = {
            __proto__: KeyboardEvent.prototype,
            type: 'keydown',
            key: key,
            target: {
                selectionStart: selectionStart,
                selectionEnd: selectionEnd,
            },
            preventDefault: () => {},
        };

        return keyboardEvent as KeyboardEvent;
    }

    function createClipboardEvent(
        text: string,
        selectionStart: number,
        selectionEnd: number
    ): ClipboardEvent {
        const clipboardEvent: any = {
            type: 'paste',
            clipboardData: {
                getData: () => {
                    return text;
                },
            },
            target: {
                selectionStart: selectionStart,
                selectionEnd: selectionEnd,
            },
            preventDefault: () => {},
        };

        return clipboardEvent as ClipboardEvent;
    }

    it('should correctly handle typing events', () => {
        let event: KeyboardEvent = createKeyboardEvent('X', 2, 2);
        expect(simulateTextChange('abcdef', event)).toEqual('abXcdef');

        event = createKeyboardEvent('X', 3, 5);
        expect(simulateTextChange('abcdef', event)).toEqual('abcXf');

        event = createKeyboardEvent('X', 0, 6);
        expect(simulateTextChange('abcdef', event)).toEqual('X');
    });

    it('should correctly handle the Backspace key', () => {
        let event: KeyboardEvent = createKeyboardEvent('Backspace', 2, 2);
        expect(simulateTextChange('abcdef', event)).toEqual('acdef');

        event = createKeyboardEvent('Backspace', 3, 5);
        expect(simulateTextChange('abcdef', event)).toEqual('abcf');

        event = createKeyboardEvent('Backspace', 0, 6);
        expect(simulateTextChange('abcdef', event)).toEqual('');
    });

    it('should correctly handle the Delete key', () => {
        let event: KeyboardEvent = createKeyboardEvent('Delete', 2, 2);
        expect(simulateTextChange('abcdef', event)).toEqual('abdef');

        event = createKeyboardEvent('Delete', 3, 5);
        expect(simulateTextChange('abcdef', event)).toEqual('abcf');

        event = createKeyboardEvent('Delete', 0, 6);
        expect(simulateTextChange('abcdef', event)).toEqual('');
    });

    it('should correctly handle pasting events', () => {
        let event: ClipboardEvent = createClipboardEvent('XXX', 2, 2);
        expect(simulateTextChange('abcdef', event)).toEqual('abXXXcdef');

        event = createClipboardEvent('XXX', 3, 5);
        expect(simulateTextChange('abcdef', event)).toEqual('abcXXXf');

        event = createClipboardEvent('XXX', 0, 6);
        expect(simulateTextChange('abcdef', event)).toEqual('XXX');
    });
});
