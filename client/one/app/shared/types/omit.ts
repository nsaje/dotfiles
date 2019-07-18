// Omit type was added natively to TypeScript in version 3.5. This type should
// be removed when updating TypeScript (https://github.com/Microsoft/TypeScript/wiki/Breaking-Changes#libdts-includes-the-omit-helper-type)
export type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;
